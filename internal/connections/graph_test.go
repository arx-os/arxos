package connections

import (
	"context"
	"database/sql"
	"testing"

	"github.com/arx-os/arxos/pkg/models"
)

func TestConnectionTypes(t *testing.T) {
	tests := []struct {
		name     string
		connType ConnectionType
		expected string
	}{
		{"Electrical", TypeElectrical, "electrical"},
		{"Data", TypeData, "data"},
		{"Water", TypeWater, "water"},
		{"Gas", TypeGas, "gas"},
		{"HVAC", TypeHVAC, "hvac"},
		{"Fiber", TypeFiber, "fiber"},
		{"Control", TypeControl, "control"},
		{"Legacy Power", ConnectionPower, "electrical"},
		{"Legacy Plumbing", ConnectionPlumbing, "water"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if string(tt.connType) != tt.expected {
				t.Errorf("expected %s, got %s", tt.expected, string(tt.connType))
			}
		})
	}
}

func TestTrace_UsesEquipmentCache(t *testing.T) {
	ctx := context.Background()

	var getEquipCalls int
	getEq := func(ctx context.Context, id string) (*models.Equipment, error) {
		getEquipCalls++
		return &models.Equipment{ID: id, Name: id}, nil
	}

	q := func(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
		return nil, nil
	}

	g := NewGraphWithHooks(getEq, q)
	_, err := g.Trace(ctx, "A", Downstream, 3)
	if err != nil {
		t.Fatalf("Trace error: %v", err)
	}

	// Expect getEquipment called small number of times (<= depth+1)
	if getEquipCalls > 4 {
		t.Errorf("expected limited equipment fetches, got %d", getEquipCalls)
	}
}

func TestFindPath_NoPanic(t *testing.T) {
	ctx := context.Background()

	getEq := func(ctx context.Context, id string) (*models.Equipment, error) {
		return &models.Equipment{ID: id, Name: id}, nil
	}

	q := func(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
		return nil, nil
	}

	g := NewGraphWithHooks(getEq, q)
	_, _ = g.FindPath(ctx, "X", "Y")
}

func TestCycleDetection_BasicLogic(t *testing.T) {
	ctx := context.Background()

	// Test basic cycle detection logic without complex DB mocking
	getEq := func(ctx context.Context, id string) (*models.Equipment, error) {
		return &models.Equipment{ID: id, Name: id}, nil
	}

	q := func(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
		return nil, nil
	}

	g := NewGraphWithHooks(getEq, q)

	// Test wouldCreateCycle with no existing connections (should not create cycle)
	hasCycle, path := g.wouldCreateCycle(ctx, "A", "B")
	if hasCycle {
		t.Errorf("expected no cycle for A->B with no existing connections, but found: %v", path)
	}

	// Test HasCycle with no connections (should not have cycles)
	hasAnyCycle, cyclePath := g.HasCycle(ctx)
	if hasAnyCycle {
		t.Errorf("expected no cycles in empty graph, but found: %v", cyclePath)
	}
}

func TestGetConnections_NilHandling(t *testing.T) {
	ctx := context.Background()

	// Test that GetConnections handles nil rows properly
	getEq := func(ctx context.Context, id string) (*models.Equipment, error) {
		return &models.Equipment{ID: id, Name: id}, nil
	}

	q := func(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
		// Return nil to test nil handling
		return nil, nil
	}

	g := NewGraphWithHooks(getEq, q)
	connections, err := g.GetConnections(ctx, "E1", Both)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(connections) != 0 {
		t.Errorf("expected 0 connections for nil rows, got %d", len(connections))
	}
}

func TestDirections(t *testing.T) {
	// Test that direction constants are properly defined
	if Upstream != "upstream" {
		t.Errorf("Upstream constant incorrect: %s", Upstream)
	}
	if Downstream != "downstream" {
		t.Errorf("Downstream constant incorrect: %s", Downstream)
	}
	if Both != "both" {
		t.Errorf("Both constant incorrect: %s", Both)
	}
}