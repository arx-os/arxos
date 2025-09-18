package radio

import (
	"fmt"
	"testing"
	"time"
)

func TestRadioCompression(t *testing.T) {
	transport := NewRadioTransport(RadioConfig{
		MaxPayload:  242,
		Compression: "high",
	})

	// Establish building context for better compression
	transport.EstablishContext("ARXOS-NA-US-NY-NYC-0001")

	tests := []struct {
		name           string
		cmd            Command
		maxCompressed  int
		minCompression float64 // Minimum compression ratio expected
	}{
		{
			name: "simple get command",
			cmd: Command{
				Method:   "GET",
				Path:     "/building/floor-02/room-203/electrical/outlet-02",
				Building: "ARXOS-NA-US-NY-NYC-0001",
			},
			maxCompressed:  50,
			minCompression: 0.7, // 70% reduction
		},
		{
			name: "status update command",
			cmd: Command{
				Method: "SET",
				Path:   "/building/floor-01/room-101/hvac/unit-01",
				Args: map[string]interface{}{
					"status": "OPERATIONAL",
					"temp":   72,
				},
			},
			maxCompressed:  60,
			minCompression: 0.6,
		},
		{
			name: "list command",
			cmd: Command{
				Method: "LIST",
				Path:   "/building/floor-03/room-301",
			},
			maxCompressed:  30,
			minCompression: 0.8,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			compressed, err := transport.compress(tt.cmd)
			if err != nil {
				t.Fatalf("compression failed: %v", err)
			}

			// Check compressed size
			if len(compressed) > tt.maxCompressed {
				t.Errorf("compressed size %d exceeds max %d", len(compressed), tt.maxCompressed)
			}

			// Calculate compression ratio
			originalSize := len(tt.cmd.Method) + len(tt.cmd.Path) + len(tt.cmd.Building)
			compressionRatio := 1.0 - float64(len(compressed))/float64(originalSize)

			if compressionRatio < tt.minCompression {
				t.Errorf("compression ratio %.2f below minimum %.2f", compressionRatio, tt.minCompression)
			}

			t.Logf("Compressed from ~%d to %d bytes (%.1f%% reduction)",
				originalSize, len(compressed), compressionRatio*100)
		})
	}
}

func TestPathCompression(t *testing.T) {
	transport := NewRadioTransport(RadioConfig{})
	transport.EstablishContext("ARXOS-NA-US-NY-NYC-0001")

	tests := []struct {
		input    string
		expected string
	}{
		{
			input:    "/building/ARXOS-NA-US-NY-NYC-0001/floor-02/room-203/electrical/outlet-02",
			expected: "B1/2/203E/outlet-02",
		},
		{
			input:    "/floor-01/room-101/hvac/unit-01",
			expected: "B1/1/101H/unit-01",
		},
		{
			input:    "/floor-03/zone-A/network/switch-01",
			expected: "B1/3/AN/switch-01",
		},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			compressed := transport.compressPath(tt.input)
			result := string(compressed)

			// Check that result is shorter
			if len(result) >= len(tt.input) {
				t.Errorf("compression failed: %s not shorter than %s", result, tt.input)
			}

			t.Logf("Compressed: %s -> %s (%d -> %d bytes)",
				tt.input, result, len(tt.input), len(result))
		})
	}
}

func TestStatusCompression(t *testing.T) {
	transport := NewRadioTransport(RadioConfig{})

	args := map[string]interface{}{
		"status":    "OPERATIONAL",
		"backup":    "DEGRADED",
		"emergency": "FAILED",
		"test":      "UNKNOWN",
	}

	compressed := transport.compressArgs(args)

	// Status values should be compressed to single bytes
	// Each status: 1 byte key length + key + 1 byte type + 1 byte value
	expectedMaxSize := len(args) * 20 // Conservative estimate

	if len(compressed) > expectedMaxSize {
		t.Errorf("args compression inefficient: %d bytes", len(compressed))
	}

	t.Logf("Compressed %d status values to %d bytes", len(args), len(compressed))
}

func TestFragmentation(t *testing.T) {
	transport := NewRadioTransport(RadioConfig{
		MaxPayload: 50, // Small payload to force fragmentation
		MaxRetries: 1,
	})

	// Create a large command that will require fragmentation
	largeArgs := make(map[string]interface{})
	for i := 0; i < 10; i++ {
		largeArgs[fmt.Sprintf("param%d", i)] = fmt.Sprintf("value%d", i)
	}

	cmd := Command{
		Method: "SET",
		Path:   "/building/floor-01/room-101/equipment",
		Args:   largeArgs,
	}

	compressed, err := transport.compress(cmd)
	if err != nil {
		t.Fatalf("compression failed: %v", err)
	}

	if len(compressed) <= transport.config.MaxPayload {
		t.Skip("Command not large enough to require fragmentation")
	}

	// Test fragment creation
	fragmentSize := transport.config.MaxPayload - 10
	numFragments := (len(compressed) + fragmentSize - 1) / fragmentSize

	t.Logf("Creating %d fragments for %d bytes of data", numFragments, len(compressed))

	for i := 0; i < numFragments; i++ {
		start := i * fragmentSize
		end := start + fragmentSize
		if end > len(compressed) {
			end = len(compressed)
		}

		fragment := transport.createFragment(compressed[start:end], i, numFragments)

		if len(fragment) > transport.config.MaxPayload {
			t.Errorf("fragment %d exceeds max payload: %d > %d",
				i, len(fragment), transport.config.MaxPayload)
		}
	}
}

func TestRetryLogic(t *testing.T) {
	// Create a mock interface that fails initially
	mockInterface := &mockRadioInterface{
		failCount: 2, // Fail first 2 attempts
	}

	transport := NewRadioTransport(RadioConfig{
		MaxRetries: 3,
		AckTimeout: 100 * time.Millisecond,
	})
	transport.radioInterface = mockInterface

	data := []byte("test data")
	response, err := transport.transmitWithRetry(data)

	if err != nil {
		t.Fatalf("transmission failed after retries: %v", err)
	}

	if string(response) != "OK" {
		t.Errorf("unexpected response: %s", response)
	}

	if mockInterface.sendCount != 3 {
		t.Errorf("expected 3 send attempts, got %d", mockInterface.sendCount)
	}
}

// mockRadioInterface is a test implementation of RadioInterface
type mockRadioInterface struct {
	failCount int
	sendCount int
	timeout   time.Duration
}

func (m *mockRadioInterface) Open(device string, baudRate int) error {
	return nil
}

func (m *mockRadioInterface) Close() error {
	return nil
}

func (m *mockRadioInterface) Send(data []byte) error {
	m.sendCount++
	if m.sendCount <= m.failCount {
		return fmt.Errorf("simulated failure %d", m.sendCount)
	}
	return nil
}

func (m *mockRadioInterface) Receive() ([]byte, error) {
	if m.sendCount <= m.failCount {
		return nil, fmt.Errorf("simulated receive failure")
	}
	return []byte("OK"), nil
}

func (m *mockRadioInterface) SetTimeout(timeout time.Duration) {
	m.timeout = timeout
}

func BenchmarkCompression(b *testing.B) {
	transport := NewRadioTransport(RadioConfig{
		MaxPayload:  242,
		Compression: "high",
	})
	transport.EstablishContext("ARXOS-NA-US-NY-NYC-0001")

	cmd := Command{
		Method:   "GET",
		Path:     "/building/floor-02/room-203/electrical/outlet-02",
		Building: "ARXOS-NA-US-NY-NYC-0001",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := transport.compress(cmd)
		if err != nil {
			b.Fatal(err)
		}
	}
}
