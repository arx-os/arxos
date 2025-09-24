package daemon

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewClient(t *testing.T) {
	client := NewClient("/tmp/test.sock")
	require.NotNil(t, client)
	assert.Equal(t, "/tmp/test.sock", client.socketPath)
	assert.Equal(t, 5*time.Second, client.timeout)
}

func TestNewClientDefault(t *testing.T) {
	client := NewClient("")
	require.NotNil(t, client)
	assert.Equal(t, "/tmp/arxos.sock", client.socketPath)
	assert.Equal(t, 5*time.Second, client.timeout)
}

func TestClientIsRunning(t *testing.T) {
	client := NewClient("/tmp/nonexistent.sock")
	require.NotNil(t, client)
	
	// Should return false for non-existent socket
	assert.False(t, client.IsRunning())
}

func TestClientSendCommand(t *testing.T) {
	client := NewClient("/tmp/nonexistent.sock")
	require.NotNil(t, client)
	
	// Should fail to connect to non-existent daemon
	response, err := client.SendCommand("test", map[string]interface{}{"key": "value"})
	assert.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "failed to connect")
}

func TestClientSendCommandWithTimeout(t *testing.T) {
	// Create client with very short timeout
	client := &Client{
		socketPath: "/tmp/nonexistent.sock",
		timeout:    1 * time.Millisecond,
	}
	
	// Should timeout quickly
	start := time.Now()
	response, err := client.SendCommand("test", map[string]interface{}{"key": "value"})
	duration := time.Since(start)
	
	assert.Error(t, err)
	assert.Nil(t, response)
	assert.Less(t, duration, 100*time.Millisecond) // Should timeout quickly
}

func TestClientConcurrentAccess(t *testing.T) {
	client := NewClient("/tmp/nonexistent.sock")
	require.NotNil(t, client)
	
	// Test concurrent access to IsRunning
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func() {
			result := client.IsRunning()
			assert.False(t, result) // Should always be false for non-existent socket
			done <- true
		}()
	}
	
	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}
}
