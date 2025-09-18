package middleware

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestInputValidation(t *testing.T) {
	handler := InputValidation(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	t.Run("allows valid request", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodPost, "/test", strings.NewReader(`{"test":"data"}`))
		req.Header.Set("Content-Type", "application/json")
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)

		assert.Equal(t, http.StatusOK, rec.Code)
	})

	t.Run("rejects oversized request", func(t *testing.T) {
		body := strings.Repeat("a", MaxRequestSize+1)
		req := httptest.NewRequest(http.MethodPost, "/test", strings.NewReader(body))
		req.ContentLength = int64(len(body))
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)

		assert.Equal(t, http.StatusBadRequest, rec.Code)
	})

	t.Run("requires content-type for POST", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodPost, "/test", strings.NewReader(`{"test":"data"}`))
		// No Content-Type header
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)

		assert.Equal(t, http.StatusBadRequest, rec.Code)
	})
}

func TestValidateEmail(t *testing.T) {
	tests := []struct {
		name     string
		email    string
		expected bool
	}{
		{"Valid simple email", "test@example.com", true},
		{"Valid email with subdomain", "user@mail.example.com", true},
		{"Valid email with plus", "user+tag@example.com", true},
		{"Valid email with dash", "user-name@example.com", true},
		{"Empty email", "", false},
		{"No @ symbol", "testexample.com", false},
		{"Multiple @ symbols", "test@@example.com", false},
		{"No domain", "test@", false},
		{"No local part", "@example.com", false},
		{"Invalid characters", "test@exam ple.com", false},
		{"Too long email", strings.Repeat("a", 250) + "@example.com", false},
		{"Invalid international domain", "test@münchen.de", false}, // Basic regex doesn't support unicode
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateEmail(tt.email)
			if tt.expected {
				assert.NoError(t, err)
			} else {
				assert.Error(t, err)
			}
		})
	}
}

func TestValidatePassword(t *testing.T) {
	tests := []struct {
		name     string
		password string
		wantErr  bool
		errMsg   string
	}{
		{"Valid strong password", "MySecure123!", false, ""},
		{"Valid password minimum length", "Test123!", false, ""},
		{"Too short", "Test1!", true, "at least 8 characters"},
		{"No uppercase", "test123!", true, "uppercase, lowercase, and numbers"},
		{"No lowercase", "TEST123!", true, "uppercase, lowercase, and numbers"},
		{"No digit", "TestTest!", true, "uppercase, lowercase, and numbers"},
		{"No special char", "TestTest123", false, ""}, // Password validation doesn't require special chars
		{"Empty password", "", true, "password is required"},
		{"Only spaces", "        ", true, "uppercase, lowercase, and numbers"},
		{"Very long password", strings.Repeat("A", 100) + "a1!", false, ""},
		{"Unicode characters", "TestÜnicöde123!", false, ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidatePassword(tt.password)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errMsg)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestValidateID(t *testing.T) {
	tests := []struct {
		name     string
		id       string
		expected bool
	}{
		{"Valid alphanumeric ID", "abc123", true},
		{"Valid with dashes", "user-123", true},
		{"Valid with underscores", "user_123", true},
		{"Valid UUID format", "550e8400-e29b-41d4-a716-446655440000", true},
		{"Empty ID", "", false},
		{"Too long ID", strings.Repeat("a", 129), false}, // ValidateID allows up to 128 chars
		{"Invalid characters", "user@123", false},
		{"Only special chars", "---", true}, // ValidateID allows dashes
		{"Spaces in ID", "user 123", false},
		{"SQL injection attempt", "'; DROP TABLE users; --", false},
		{"Script tag", "<script>alert('xss')</script>", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateID(tt.id)
			if tt.expected {
				assert.NoError(t, err)
			} else {
				assert.Error(t, err)
			}
		})
	}
}

func TestValidateJSON(t *testing.T) {
	type TestStruct struct {
		Name  string `json:"name"`
		Email string `json:"email"`
		Age   int    `json:"age"`
	}

	tests := []struct {
		name     string
		jsonData string
		target   interface{}
		wantErr  bool
		errMsg   string
	}{
		{
			"Valid JSON",
			`{"name":"John","email":"john@example.com","age":30}`,
			&TestStruct{},
			false,
			"",
		},
		{
			"Invalid JSON syntax",
			`{"name":"John","email":"john@example.com","age":}`,
			&TestStruct{},
			true,
			"invalid character",
		},
		{
			"Empty JSON",
			``,
			&TestStruct{},
			true,
			"JSON cannot be empty",
		},
		{
			"Type mismatch",
			`{"name":"John","email":"john@example.com","age":"thirty"}`,
			&TestStruct{},
			false, // ValidateJSON only checks syntax, not types
			"",
		},
		{
			"Malicious JSON with script",
			`{"name":"<script>alert('xss')</script>","email":"test@example.com","age":25}`,
			&TestStruct{},
			false, // Should parse but be sanitized elsewhere
			"",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateJSON(tt.jsonData)
			if tt.wantErr {
				assert.Error(t, err)
				if tt.errMsg != "" {
					assert.Contains(t, err.Error(), tt.errMsg)
				}
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSanitizeString(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{"Clean string", "hello world", "hello world"},
		{"Script tag", "<script>alert('xss')</script>", "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"}, // SanitizeString HTML escapes
		{"HTML tags", "<div>content</div>", "&lt;div&gt;content&lt;/div&gt;"},
		{"Mixed content", "Hello <b>world</b> <script>bad()</script>", "Hello &lt;b&gt;world&lt;/b&gt; &lt;script&gt;bad()&lt;/script&gt;"},
		{"SQL injection", "'; DROP TABLE users; --", "&#39;; DROP TABLE users; --"}, // HTML escapes quotes
		{"Empty string", "", ""},
		{"Whitespace trim", "  hello world  ", "hello world"},
		{"Null bytes", "hello\x00world", "helloworld"}, // SanitizeString removes null bytes
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := SanitizeString(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}
