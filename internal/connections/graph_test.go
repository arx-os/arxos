package connections

import (
	"context"
	"database/sql"
	"testing"

	"github.com/arx-os/arxos/pkg/models"
)


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
