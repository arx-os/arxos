package middleware

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestValidationMiddleware_Creation(t *testing.T) {
	vm := NewValidationMiddleware()
	assert.NotNil(t, vm)
	assert.Equal(t, int64(10*1024*1024), vm.maxBodySize)
	assert.Equal(t, 8192, vm.maxHeaderSize)
	assert.Contains(t, vm.allowedMethods, http.MethodGet)
	assert.Contains(t, vm.allowedMethods, http.MethodPost)
}

func TestValidationMiddleware_AllowedMethods(t *testing.T) {
	vm := NewValidationMiddleware()
	
	tests := []struct {
		name           string
		method         string
		expectAllowed  bool
	}{
		{"GET allowed", http.MethodGet, true},
		{"POST allowed", http.MethodPost, true},
		{"PUT allowed", http.MethodPut, true},
		{"PATCH allowed", http.MethodPatch, true},
		{"DELETE allowed", http.MethodDelete, true},
		{"OPTIONS allowed", http.MethodOptions, true},
		{"HEAD not allowed", http.MethodHead, false},
		{"TRACE not allowed", http.MethodTrace, false},
		{"CONNECT not allowed", http.MethodConnect, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(tt.method, "/test", nil)
			recorder := httptest.NewRecorder()
			
			called := false
			handler := vm.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				called = true
				w.WriteHeader(http.StatusOK)
			}))
			
			handler.ServeHTTP(recorder, req)
			
			if tt.expectAllowed {
				assert.True(t, called, "Handler should be called for allowed method")
				assert.Equal(t, http.StatusOK, recorder.Code)
			} else {
				assert.False(t, called, "Handler should not be called for disallowed method")
				assert.Equal(t, http.StatusMethodNotAllowed, recorder.Code)
			}
		})
	}
}

func TestValidationMiddleware_RequestSizeValidation(t *testing.T) {
	vm := NewValidationMiddleware()
	
	tests := []struct {
		name           string
		bodySize       int
		headerSize     int
		expectRejected bool
		expectedCode   int
	}{
		{"Normal request", 1024, 100, false, http.StatusOK},
		{"Large but acceptable body", 5*1024*1024, 100, false, http.StatusOK},
		{"Too large body", 15*1024*1024, 100, true, http.StatusRequestEntityTooLarge},
		{"Large but acceptable headers", 1024, 4096, false, http.StatusOK},
		{"Too large headers", 1024, 10000, true, http.StatusBadRequest},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create request with specified body size
			body := strings.Repeat("a", tt.bodySize)
			req := httptest.NewRequest(http.MethodPost, "/test", strings.NewReader(body))
			
			// Add headers to reach specified header size
			headerValue := strings.Repeat("x", tt.headerSize)
			req.Header.Set("X-Test-Header", headerValue)
			
			recorder := httptest.NewRecorder()
			
			called := false
			handler := vm.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				called = true
				w.WriteHeader(http.StatusOK)
			}))
			
			handler.ServeHTTP(recorder, req)
			
			if tt.expectRejected {
				assert.False(t, called, "Handler should not be called for oversized request")
				assert.Equal(t, tt.expectedCode, recorder.Code)
			} else {
				assert.True(t, called, "Handler should be called for normal request")
				assert.Equal(t, tt.expectedCode, recorder.Code)
			}
		})
	}
}

func TestValidationMiddleware_HeaderPassthrough(t *testing.T) {
	vm := NewValidationMiddleware()
	
	req := httptest.NewRequest(http.MethodPost, "/test", nil)
	// Add headers (middleware validates but doesn't modify them)
	req.Header.Set("X-Script", "<script>alert('xss')</script>")
	req.Header.Set("X-Normal", "normal-value")
	req.Header.Set("Content-Length", "100")
	
	recorder := httptest.NewRecorder()
	
	var capturedRequest *http.Request
	handler := vm.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedRequest = r
		w.WriteHeader(http.StatusOK)
	}))
	
	handler.ServeHTTP(recorder, req)
	
	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.NotNil(t, capturedRequest)
	
	// Headers are passed through unchanged (validation doesn't modify them)
	scriptHeader := capturedRequest.Header.Get("X-Script")
	assert.Equal(t, "<script>alert('xss')</script>", scriptHeader)
	
	// All headers should be preserved exactly
	assert.Equal(t, "normal-value", capturedRequest.Header.Get("X-Normal"))
	assert.Equal(t, "100", capturedRequest.Header.Get("Content-Length"))
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
			result := ValidateEmail(tt.email)
			assert.Equal(t, tt.expected, result)
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
		{"Empty password", "", true, "at least 8 characters"},
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
			result := ValidateID(tt.id)
			assert.Equal(t, tt.expected, result)
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
			"EOF",
		},
		{
			"Type mismatch",
			`{"name":"John","email":"john@example.com","age":"thirty"}`,
			&TestStruct{},
			true,
			"cannot unmarshal string into Go struct field",
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
			err := ValidateJSON([]byte(tt.jsonData), tt.target)
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
		{"Script tag", "<script>alert('xss')</script>", "<script>alert('xss')</script>"}, // SanitizeString doesn't remove HTML
		{"HTML tags", "<div>content</div>", "<div>content</div>"},
		{"Mixed content", "Hello <b>world</b> <script>bad()</script>", "Hello <b>world</b> <script>bad()</script>"},
		{"SQL injection", "'; DROP TABLE users; --", "'; DROP TABLE users; --"}, // Basic sanitize doesn't handle SQL
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

func TestValidationMiddleware_ContextPropagation(t *testing.T) {
	vm := NewValidationMiddleware()
	
	req := httptest.NewRequest(http.MethodPost, "/test", nil)
	req.Header.Set("X-Request-ID", "test-123")
	
	// Add some context value
	ctx := context.WithValue(req.Context(), "test-key", "test-value")
	req = req.WithContext(ctx)
	
	recorder := httptest.NewRecorder()
	
	var capturedContext context.Context
	handler := vm.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedContext = r.Context()
		w.WriteHeader(http.StatusOK)
	}))
	
	handler.ServeHTTP(recorder, req)
	
	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.NotNil(t, capturedContext)
	
	// Verify context is properly propagated
	value := capturedContext.Value("test-key")
	assert.Equal(t, "test-value", value)
}

func TestValidationMiddleware_Integration(t *testing.T) {
	vm := NewValidationMiddleware()
	
	// Test a complete request with JSON body
	requestData := map[string]interface{}{
		"name":  "John Doe",
		"email": "john@example.com",
		"age":   30,
	}
	
	jsonData, err := json.Marshal(requestData)
	require.NoError(t, err)
	
	req := httptest.NewRequest(http.MethodPost, "/api/users", bytes.NewReader(jsonData))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Request-ID", "integration-test-123")
	
	recorder := httptest.NewRecorder()
	
	var receivedData map[string]interface{}
	handler := vm.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Verify we can read the body
		decoder := json.NewDecoder(r.Body)
		err := decoder.Decode(&receivedData)
		assert.NoError(t, err)
		
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(map[string]string{"status": "created"})
	}))
	
	handler.ServeHTTP(recorder, req)
	
	assert.Equal(t, http.StatusCreated, recorder.Code)
	assert.Equal(t, "application/json", recorder.Header().Get("Content-Type"))
	
	// Verify data was received correctly
	assert.Equal(t, "John Doe", receivedData["name"])
	assert.Equal(t, "john@example.com", receivedData["email"])
	assert.Equal(t, float64(30), receivedData["age"]) // JSON numbers are float64
}