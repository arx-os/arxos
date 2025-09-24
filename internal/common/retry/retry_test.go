package retry

import (
	"context"
	"errors"
	"fmt"
	"testing"
	"time"
)

// Mock operation that fails a specific number of times then succeeds
type mockOperation struct {
	failCount    int
	currentCount int
	finalError   error
}

func (m *mockOperation) execute(ctx context.Context) error {
	m.currentCount++
	if m.currentCount <= m.failCount {
		if m.finalError != nil && m.currentCount == m.failCount {
			return m.finalError
		}
		return errors.New("mock error")
	}
	return nil
}

// Mock operation that returns data
type mockDataOperation struct {
	failCount    int
	currentCount int
	data         interface{}
	finalError   error
}

func (m *mockDataOperation) execute(ctx context.Context) (interface{}, error) {
	m.currentCount++
	if m.currentCount <= m.failCount {
		if m.finalError != nil && m.currentCount == m.failCount {
			return nil, m.finalError
		}
		return nil, errors.New("mock error")
	}
	return m.data, nil
}

func TestDefaultConfig(t *testing.T) {
	config := DefaultConfig()
	
	if config.MaxAttempts != 3 {
		t.Errorf("Expected MaxAttempts=3, got %d", config.MaxAttempts)
	}
	if config.InitialDelay != 1*time.Second {
		t.Errorf("Expected InitialDelay=1s, got %v", config.InitialDelay)
	}
	if config.MaxDelay != 30*time.Second {
		t.Errorf("Expected MaxDelay=30s, got %v", config.MaxDelay)
	}
	if config.Multiplier != 2.0 {
		t.Errorf("Expected Multiplier=2.0, got %f", config.Multiplier)
	}
	if config.Strategy != StrategyExponential {
		t.Errorf("Expected StrategyExponential, got %v", config.Strategy)
	}
	if !config.Jitter {
		t.Error("Expected Jitter=true")
	}
	if config.RetryIf == nil {
		t.Error("Expected RetryIf function to be set")
	}
}

func TestIsRetryable(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{
			name:     "nil error",
			err:      nil,
			expected: false,
		},
		{
			name:     "permanent error",
			err:      Permanent{Err: errors.New("permanent")},
			expected: false,
		},
		{
			name:     "context canceled",
			err:      context.Canceled,
			expected: false,
		},
		{
			name:     "context deadline exceeded",
			err:      context.DeadlineExceeded,
			expected: false,
		},
		{
			name:     "regular error",
			err:      errors.New("regular error"),
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsRetryable(tt.err)
			if result != tt.expected {
				t.Errorf("IsRetryable(%v) = %v, expected %v", tt.err, result, tt.expected)
			}
		})
	}
}

func TestIsPermanent(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{
			name:     "permanent error",
			err:      Permanent{Err: errors.New("permanent")},
			expected: true,
		},
		{
			name:     "regular error",
			err:      errors.New("regular error"),
			expected: false,
		},
		{
			name:     "nil error",
			err:      nil,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsPermanent(tt.err)
			if result != tt.expected {
				t.Errorf("IsPermanent(%v) = %v, expected %v", tt.err, result, tt.expected)
			}
		})
	}
}

func TestDo_Success(t *testing.T) {
	config := Config{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Millisecond,
		MaxDelay:     10 * time.Millisecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx := context.Background()
	op := &mockOperation{failCount: 0}

	result := Do(ctx, op.execute, config)

	if !result.Success {
		t.Error("Expected success")
	}
	if result.Attempts != 1 {
		t.Errorf("Expected 1 attempt, got %d", result.Attempts)
	}
	if result.LastError != nil {
		t.Errorf("Expected no error, got %v", result.LastError)
	}
}

func TestDo_RetrySuccess(t *testing.T) {
	config := Config{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Millisecond,
		MaxDelay:     10 * time.Millisecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx := context.Background()
	op := &mockOperation{failCount: 2}

	result := Do(ctx, op.execute, config)

	if !result.Success {
		t.Errorf("Expected success, got error: %v", result.LastError)
	}
	if result.Attempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", result.Attempts)
	}
	if result.LastError != nil {
		t.Errorf("Expected no error, got %v", result.LastError)
	}
}

func TestDo_MaxAttemptsReached(t *testing.T) {
	config := Config{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Millisecond,
		MaxDelay:     10 * time.Millisecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx := context.Background()
	op := &mockOperation{failCount: 5} // More than max attempts

	result := Do(ctx, op.execute, config)

	if result.Success {
		t.Error("Expected failure")
	}
	if result.Attempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", result.Attempts)
	}
	if !errors.Is(result.LastError, ErrMaxAttemptsReached) {
		t.Errorf("Expected ErrMaxAttemptsReached, got %v", result.LastError)
	}
}

func TestDo_PermanentError(t *testing.T) {
	config := Config{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Millisecond,
		MaxDelay:     10 * time.Millisecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx := context.Background()
	permanentErr := Permanent{Err: errors.New("permanent error")}
	op := &mockOperation{failCount: 1, finalError: permanentErr}

	result := Do(ctx, op.execute, config)

	if result.Success {
		t.Error("Expected failure")
	}
	if result.Attempts != 1 {
		t.Errorf("Expected 1 attempt, got %d", result.Attempts)
	}
	if !errors.Is(result.LastError, permanentErr) {
		t.Errorf("Expected permanent error, got %v", result.LastError)
	}
}

func TestDo_ContextCanceled(t *testing.T) {
	config := Config{
		MaxAttempts:  3,
		InitialDelay: 10 * time.Millisecond,
		MaxDelay:     50 * time.Millisecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx, cancel := context.WithCancel(context.Background())
	op := &mockOperation{failCount: 5}

	// Cancel context after first attempt
	go func() {
		time.Sleep(5 * time.Millisecond)
		cancel()
	}()

	result := Do(ctx, op.execute, config)

	if result.Success {
		t.Error("Expected failure")
	}
	if !errors.Is(result.LastError, ErrContextCanceled) {
		t.Errorf("Expected ErrContextCanceled, got %v", result.LastError)
	}
}

func TestDoWithData_Success(t *testing.T) {
	config := Config{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Millisecond,
		MaxDelay:     10 * time.Millisecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx := context.Background()
	expectedData := "test data"
	op := &mockDataOperation{failCount: 0, data: expectedData}

	data, result := DoWithData(ctx, op.execute, config)

	if !result.Success {
		t.Error("Expected success")
	}
	if data != expectedData {
		t.Errorf("Expected data %v, got %v", expectedData, data)
	}
	if result.Attempts != 1 {
		t.Errorf("Expected 1 attempt, got %d", result.Attempts)
	}
}

func TestDoWithData_RetrySuccess(t *testing.T) {
	config := Config{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Millisecond,
		MaxDelay:     10 * time.Millisecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx := context.Background()
	expectedData := "test data"
	op := &mockDataOperation{failCount: 2, data: expectedData}

	data, result := DoWithData(ctx, op.execute, config)

	if !result.Success {
		t.Error("Expected success")
	}
	if data != expectedData {
		t.Errorf("Expected data %v, got %v", expectedData, data)
	}
	if result.Attempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", result.Attempts)
	}
}

func TestCalculateDelay_Exponential(t *testing.T) {
	config := Config{
		InitialDelay: 100 * time.Millisecond,
		MaxDelay:     1 * time.Second,
		Multiplier:   2.0,
		Strategy:     StrategyExponential,
		Jitter:       false,
	}

	tests := []struct {
		attempt int
		expected time.Duration
	}{
		{1, 100 * time.Millisecond},
		{2, 200 * time.Millisecond},
		{3, 400 * time.Millisecond},
		{4, 800 * time.Millisecond},
		{5, 1 * time.Second}, // Capped at MaxDelay
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("attempt_%d", tt.attempt), func(t *testing.T) {
			delay := calculateDelay(tt.attempt, config)
			if delay != tt.expected {
				t.Errorf("Expected delay %v, got %v", tt.expected, delay)
			}
		})
	}
}

func TestCalculateDelay_Linear(t *testing.T) {
	config := Config{
		InitialDelay: 100 * time.Millisecond,
		MaxDelay:     1 * time.Second,
		Multiplier:   2.0,
		Strategy:     StrategyLinear,
		Jitter:       false,
	}

	tests := []struct {
		attempt int
		expected time.Duration
	}{
		{1, 100 * time.Millisecond},
		{2, 200 * time.Millisecond},
		{3, 300 * time.Millisecond},
		{4, 400 * time.Millisecond},
		{5, 500 * time.Millisecond},
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("attempt_%d", tt.attempt), func(t *testing.T) {
			delay := calculateDelay(tt.attempt, config)
			if delay != tt.expected {
				t.Errorf("Expected delay %v, got %v", tt.expected, delay)
			}
		})
	}
}

func TestCalculateDelay_Constant(t *testing.T) {
	config := Config{
		InitialDelay: 100 * time.Millisecond,
		MaxDelay:     1 * time.Second,
		Multiplier:   2.0,
		Strategy:     StrategyConstant,
		Jitter:       false,
	}

	tests := []struct {
		attempt int
		expected time.Duration
	}{
		{1, 100 * time.Millisecond},
		{2, 100 * time.Millisecond},
		{3, 100 * time.Millisecond},
		{4, 100 * time.Millisecond},
		{5, 100 * time.Millisecond},
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("attempt_%d", tt.attempt), func(t *testing.T) {
			delay := calculateDelay(tt.attempt, config)
			if delay != tt.expected {
				t.Errorf("Expected delay %v, got %v", tt.expected, delay)
			}
		})
	}
}

func TestRetrier(t *testing.T) {
	config := Config{
		MaxAttempts:  2,
		InitialDelay: 1 * time.Millisecond,
		MaxDelay:     10 * time.Millisecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	retrier := NewRetrier(config)
	ctx := context.Background()
	op := &mockOperation{failCount: 1}

	result := retrier.Do(ctx, op.execute)

	if !result.Success {
		t.Error("Expected success")
	}
	if result.Attempts != 2 {
		t.Errorf("Expected 2 attempts, got %d", result.Attempts)
	}
}

func TestHTTPRetryConfig(t *testing.T) {
	config := DefaultHTTPRetryConfig()
	
	if config.MaxAttempts != 3 {
		t.Errorf("Expected MaxAttempts=3, got %d", config.MaxAttempts)
	}
	
	expectedCodes := []int{408, 429, 500, 502, 503, 504}
	if len(config.RetryStatusCodes) != len(expectedCodes) {
		t.Errorf("Expected %d retry status codes, got %d", len(expectedCodes), len(config.RetryStatusCodes))
	}
	
	for _, code := range expectedCodes {
		found := false
		for _, retryCode := range config.RetryStatusCodes {
			if retryCode == code {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected retry status code %d not found", code)
		}
	}
}

func TestIsRetryableHTTPStatus(t *testing.T) {
	retryCodes := []int{408, 429, 500, 502, 503, 504}
	
	tests := []struct {
		statusCode int
		expected   bool
	}{
		{200, false},
		{404, false},
		{408, true},
		{429, true},
		{500, true},
		{502, true},
		{503, true},
		{504, true},
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("status_%d", tt.statusCode), func(t *testing.T) {
			result := IsRetryableHTTPStatus(tt.statusCode, retryCodes)
			if result != tt.expected {
				t.Errorf("IsRetryableHTTPStatus(%d) = %v, expected %v", tt.statusCode, result, tt.expected)
			}
		})
	}
}

func TestDBRetryConfig(t *testing.T) {
	config := DefaultDBRetryConfig()
	
	if config.MaxAttempts != 3 {
		t.Errorf("Expected MaxAttempts=3, got %d", config.MaxAttempts)
	}
	if config.InitialDelay != 100*time.Millisecond {
		t.Errorf("Expected InitialDelay=100ms, got %v", config.InitialDelay)
	}
	if config.MaxDelay != 2*time.Second {
		t.Errorf("Expected MaxDelay=2s, got %v", config.MaxDelay)
	}
	if config.RetryIf == nil {
		t.Error("Expected RetryIf function to be set")
	}
}

func TestIsRetryableDBError(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{
			name:     "nil error",
			err:      nil,
			expected: false,
		},
		{
			name:     "connection refused",
			err:      errors.New("connection refused"),
			expected: true,
		},
		{
			name:     "connection reset",
			err:      errors.New("connection reset by peer"),
			expected: true,
		},
		{
			name:     "broken pipe",
			err:      errors.New("broken pipe"),
			expected: true,
		},
		{
			name:     "deadlock",
			err:      errors.New("deadlock detected"),
			expected: true,
		},
		{
			name:     "lock timeout",
			err:      errors.New("lock timeout"),
			expected: true,
		},
		{
			name:     "database is locked",
			err:      errors.New("database is locked"),
			expected: true,
		},
		{
			name:     "temporary error",
			err:      errors.New("temporary failure"),
			expected: true,
		},
		{
			name:     "try again",
			err:      errors.New("try again later"),
			expected: true,
		},
		{
			name:     "regular error",
			err:      errors.New("regular error"),
			expected: true, // Regular errors are retryable by default
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsRetryableDBError(tt.err)
			if result != tt.expected {
				t.Errorf("IsRetryableDBError(%v) = %v, expected %v", tt.err, result, tt.expected)
			}
		})
	}
}

func TestCircuitBreaker(t *testing.T) {
	cb := NewCircuitBreaker(2, 100*time.Millisecond)
	ctx := context.Background()

	// Test successful operation
	err := cb.Call(ctx, func(ctx context.Context) error {
		return nil
	})
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	// Test failures that should trigger circuit breaker
	for i := 0; i < 2; i++ {
		err := cb.Call(ctx, func(ctx context.Context) error {
			return errors.New("test error")
		})
		if err == nil {
			t.Error("Expected error")
		}
	}

	// Circuit should be open now
	err = cb.Call(ctx, func(ctx context.Context) error {
		return nil
	})
	if err == nil {
		t.Error("Expected circuit breaker to be open")
	}
	if err.Error() != "circuit breaker is open" {
		t.Errorf("Expected 'circuit breaker is open', got %v", err)
	}

	// Wait for reset timeout
	time.Sleep(150 * time.Millisecond)

	// Test half-open state
	err = cb.Call(ctx, func(ctx context.Context) error {
		return nil
	})
	if err != nil {
		t.Errorf("Expected no error after reset, got %v", err)
	}
}

func TestCircuitBreaker_StateTransitions(t *testing.T) {
	cb := NewCircuitBreaker(1, 50*time.Millisecond)
	ctx := context.Background()

	// Start closed
	if cb.state != CircuitClosed {
		t.Errorf("Expected CircuitClosed, got %v", cb.state)
	}

	// Fail once to open circuit
	err := cb.Call(ctx, func(ctx context.Context) error {
		return errors.New("test error")
	})
	if err == nil {
		t.Error("Expected error")
	}

	// Should be open now
	if cb.state != CircuitOpen {
		t.Errorf("Expected CircuitOpen, got %v", cb.state)
	}

	// Wait for reset
	time.Sleep(75 * time.Millisecond)

	// Call to trigger transition to half-open
	err = cb.Call(ctx, func(ctx context.Context) error {
		return nil
	})
	if err != nil {
		t.Errorf("Expected no error after reset, got %v", err)
	}

	// Should be closed now (successful call in half-open state)
	if cb.state != CircuitClosed {
		t.Errorf("Expected CircuitClosed, got %v", cb.state)
	}

	// Success should close circuit
	err = cb.Call(ctx, func(ctx context.Context) error {
		return nil
	})
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	if cb.state != CircuitClosed {
		t.Errorf("Expected CircuitClosed, got %v", cb.state)
	}
}

// Benchmark tests
func BenchmarkDo_Success(b *testing.B) {
	config := Config{
		MaxAttempts:  1,
		InitialDelay: 1 * time.Microsecond,
		MaxDelay:     1 * time.Microsecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx := context.Background()
	op := &mockOperation{failCount: 0}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Do(ctx, op.execute, config)
	}
}

func BenchmarkDo_Retry(b *testing.B) {
	config := Config{
		MaxAttempts:  3,
		InitialDelay: 1 * time.Microsecond,
		MaxDelay:     1 * time.Microsecond,
		Strategy:     StrategyConstant,
		Jitter:       false,
		RetryIf:      IsRetryable,
	}

	ctx := context.Background()
	op := &mockOperation{failCount: 2}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Do(ctx, op.execute, config)
	}
}

func BenchmarkCircuitBreaker(b *testing.B) {
	cb := NewCircuitBreaker(10, 1*time.Second)
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cb.Call(ctx, func(ctx context.Context) error {
			return nil
		})
	}
}
