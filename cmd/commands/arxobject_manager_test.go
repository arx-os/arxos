package commands

import (
	"testing"
	"time"
)

func TestNewArxObjectManager(t *testing.T) {
	buildingID := "building:test"
	manager := NewArxObjectManager(buildingID)

	if manager.BuildingID != buildingID {
		t.Errorf("Expected BuildingID %s, got %s", buildingID, manager.BuildingID)
	}

	expectedObjectsDir := buildingID + "/.arxos/objects"
	if manager.ObjectsDir != expectedObjectsDir {
		t.Errorf("Expected ObjectsDir %s, got %s", expectedObjectsDir, manager.ObjectsDir)
	}

	expectedIndexPath := buildingID + "/.arxos/objects/index.json"
	if manager.IndexPath != expectedIndexPath {
		t.Errorf("Expected IndexPath %s, got %s", expectedIndexPath, manager.IndexPath)
	}
}

func TestArxObjectMetadata_Validation(t *testing.T) {
	obj := &ArxObjectMetadata{
		ID:          "test:object:1",
		Name:        "Test Object",
		Type:        "test",
		Description: "A test object",
		Status:      "active",
		Created:     time.Now().UTC(),
		Updated:     time.Now().UTC(),
	}

	if obj.ID != "test:object:1" {
		t.Errorf("Expected ID test:object:1, got %s", obj.ID)
	}

	if obj.Name != "Test Object" {
		t.Errorf("Expected Name Test Object, got %s", obj.Name)
	}

	if obj.Type != "test" {
		t.Errorf("Expected Type test, got %s", obj.Type)
	}
}

func TestRelationshipMetadata_Creation(t *testing.T) {
	rel := RelationshipMetadata{
		ID:         "rel_1",
		Type:       "contains",
		TargetID:   "target_1",
		SourceID:   "source_1",
		Confidence: 0.9,
		CreatedAt:  time.Now().UTC(),
		Direction:  "outgoing",
	}

	if rel.ID != "rel_1" {
		t.Errorf("Expected ID rel_1, got %s", rel.ID)
	}

	if rel.Type != "contains" {
		t.Errorf("Expected Type contains, got %s", rel.Type)
	}

	if rel.Confidence != 0.9 {
		t.Errorf("Expected Confidence 0.9, got %f", rel.Confidence)
	}
}

func TestValidationMetadata_Creation(t *testing.T) {
	val := ValidationMetadata{
		ID:          "val_1",
		Timestamp:   time.Now().UTC(),
		ValidatedBy: "test_user",
		Method:      "photo",
		Confidence:  0.95,
		Status:      "approved",
	}

	if val.ID != "val_1" {
		t.Errorf("Expected ID val_1, got %s", val.ID)
	}

	if val.Method != "photo" {
		t.Errorf("Expected Method photo, got %s", val.Method)
	}

	if val.Confidence != 0.95 {
		t.Errorf("Expected Confidence 0.95, got %f", val.Confidence)
	}
}

func TestExtractBuildingID(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"building:main:floor:1", "building:main"},
		{"building:hq:system:electrical", "building:hq"},
		{"building:warehouse", "building:warehouse"},
		{"floor:1", "floor:1"},
		{"", ""},
	}

	for _, test := range tests {
		result := extractBuildingID(test.input)
		if result != test.expected {
			t.Errorf("For input '%s', expected '%s', got '%s'", test.input, test.expected, result)
		}
	}
}

func TestArxObjectLifecycle_Creation(t *testing.T) {
	now := time.Now().UTC()
	lifecycle := ArxObjectLifecycle{
		ID:      "lifecycle_1",
		Status:  "active",
		Phase:   "operational",
		Created: now,
		Updated: now,
	}

	if lifecycle.ID != "lifecycle_1" {
		t.Errorf("Expected ID lifecycle_1, got %s", lifecycle.ID)
	}

	if lifecycle.Status != "active" {
		t.Errorf("Expected Status active, got %s", lifecycle.Status)
	}

	if lifecycle.Phase != "operational" {
		t.Errorf("Expected Phase operational, got %s", lifecycle.Phase)
	}
}
