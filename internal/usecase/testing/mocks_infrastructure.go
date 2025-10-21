package testing

import (
	"github.com/arx-os/arxos/internal/domain"
	"github.com/stretchr/testify/mock"
)

// =============================================================================
// Infrastructure Mocks
// =============================================================================

// MockLogger is a mock implementation of domain.Logger
type MockLogger struct {
	mock.Mock
}

func (m *MockLogger) Info(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Error(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Debug(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) Warn(msg string, fields ...any) {
	m.Called(msg, fields)
}

func (m *MockLogger) WithFields(fields map[string]any) domain.Logger {
	args := m.Called(fields)
	return args.Get(0).(domain.Logger)
}

func (m *MockLogger) WithField(key string, value any) domain.Logger {
	args := m.Called(key, value)
	return args.Get(0).(domain.Logger)
}

func (m *MockLogger) Fatal(msg string, fields ...any) {
	m.Called(msg, fields)
}
