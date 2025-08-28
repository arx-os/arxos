package resolution

import (
	"testing"
)

func TestSystemResolver(t *testing.T) {
	resolver := NewMockSystemResolver()
	
	// Test root path - should return system summaries
	objects, err := resolver.ResolveSystemPath("/")
	if err != nil {
		t.Fatalf("Failed to resolve root path: %v", err)
	}
	
	if len(objects) != 10 {
		t.Errorf("Expected 10 system objects for root path, got %d", len(objects))
	}
	
	// Test specific system path
	objects, err = resolver.ResolveSystemPath("/electrical")
	if err != nil {
		t.Fatalf("Failed to resolve /electrical path: %v", err)
	}
	
	// Mock database returns empty results, so we should get empty slice
	if len(objects) != 0 {
		t.Errorf("Expected 0 objects for /electrical (mock database), got %d", len(objects))
	}
}

func TestSystemStats(t *testing.T) {
	resolver := NewMockSystemResolver()
	
	stats, err := resolver.GetSystemStats("/electrical")
	if err != nil {
		t.Fatalf("Failed to get system stats: %v", err)
	}
	
	if stats.Path != "/electrical" {
		t.Errorf("Expected path '/electrical', got '%s'", stats.Path)
	}
	
	if stats.TotalObjects != 0 {
		t.Errorf("Expected 0 total objects (mock database), got %d", stats.TotalObjects)
	}
}

func TestArxObjectUnified(t *testing.T) {
	obj := &ArxObjectUnified{
		ID:     "test-object",
		Type:   "outlet",
		Name:   "Test Outlet",
		System: "electrical",
		Path:   "/electrical/outlet/test",
	}
	
	if obj.GetID() != "test-object" {
		t.Errorf("Expected ID 'test-object', got '%s'", obj.GetID())
	}
	
	if obj.GetSystem() != "electrical" {
		t.Errorf("Expected system 'electrical', got '%s'", obj.GetSystem())
	}
	
	if obj.GetPath() != "/electrical/outlet/test" {
		t.Errorf("Expected path '/electrical/outlet/test', got '%s'", obj.GetPath())
	}
}