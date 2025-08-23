package types

import (
	"testing"
)

func TestConnectionType_String(t *testing.T) {
	testCases := []struct {
		connType ConnectionType
		expected string
	}{
		{ConnectionNone, "none"},
		{ConnectionEndToEnd, "end-to-end"},
		{ConnectionOverlapping, "overlapping"},
		{ConnectionIntersecting, "intersecting"},
		{ConnectionAdjacent, "adjacent"},
	}

	for _, tc := range testCases {
		if tc.connType.String() != tc.expected {
			t.Errorf("ConnectionType %v: expected '%s', got '%s'",
				tc.connType, tc.expected, tc.connType.String())
		}
	}
}

func TestNewWallConnection(t *testing.T) {
	wall1ID := uint64(1)
	wall2ID := uint64(2)
	connType := ConnectionEndToEnd

	connection := NewWallConnection(wall1ID, wall2ID, connType)

	if connection.Wall1ID != wall1ID {
		t.Errorf("Expected Wall1ID %d, got %d", wall1ID, connection.Wall1ID)
	}

	if connection.Wall2ID != wall2ID {
		t.Errorf("Expected Wall2ID %d, got %d", wall2ID, connection.Wall2ID)
	}

	if connection.Type != connType {
		t.Errorf("Expected Type %v, got %v", connType, connection.Type)
	}

	if connection.Confidence != 0.0 {
		t.Errorf("Expected Confidence 0.0, got %.2f", connection.Confidence)
	}

	if connection.Distance != 0.0 {
		t.Errorf("Expected Distance 0.0, got %.2f", connection.Distance)
	}

	if connection.Angle != 0.0 {
		t.Errorf("Expected Angle 0.0, got %.2f", connection.Angle)
	}
}
