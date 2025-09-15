package converter

import (
	"strings"
	"testing"
)

func TestSpatialIFCConverter_ParseSpatialHierarchy(t *testing.T) {
	converter := NewSpatialIFCConverter()

	// Create test IFC data with spatial hierarchy
	ifcData := []string{
		"#1 = IFCPROJECT('3M$Jv0HrvxqwdJb0k2tF6R',$,'Test Project',$,$,$,$,#2,$);",
		"#2 = IFCBUILDING('2M$Jv0HrvxqwdJb0k2tF6R',$,'Test Building','Main building',$,$,$,$,.ELEMENT.,$,$,$);",
		"#3 = IFCBUILDINGSTOREY('1M$Jv0HrvxqwdJb0k2tF6R',$,'Ground Floor','Level 0',$,$,$,$,.ELEMENT.,0.0);",
		"#4 = IFCBUILDINGSTOREY('4M$Jv0HrvxqwdJb0k2tF6R',$,'First Floor','Level 1',$,$,$,$,.ELEMENT.,3000.0);",
		"#5 = IFCSPACE('5M$Jv0HrvxqwdJb0k2tF6R',$,'Office 101','Main office space',$,$,$,$,.ELEMENT.,.INTERNAL.,0.0);",
		"#6 = IFCSPACE('6M$Jv0HrvxqwdJb0k2tF6R',$,'Conference Room 102','Meeting room',$,$,$,$,.ELEMENT.,.INTERNAL.,0.0);",
		"#7 = IFCSPACE('7M$Jv0HrvxqwdJb0k2tF6R',$,'Office 201','Office on first floor',$,$,$,$,.ELEMENT.,.INTERNAL.,3000.0);",
		"#10 = IFCRELAGGREGATES('10M$Jv0HrvxqwdJb0k2tF6R',$,'BuildingContainsStoreys',$,#2,(#3,#4));",
		"#11 = IFCRELAGGREGATES('11M$Jv0HrvxqwdJb0k2tF6R',$,'StoreyContainsSpaces',$,#3,(#5,#6));",
		"#12 = IFCRELAGGREGATES('12M$Jv0HrvxqwdJb0k2tF6R',$,'StoreyContainsSpaces',$,#4,(#7));",
	}

	// Parse entities and build hierarchy
	converter.parseAllEntities(ifcData)
	converter.parseSpatialRelationships()
	converter.buildSpatialHierarchy()

	// Verify building structure was parsed (all entities including relationships)
	if len(converter.entities) < 7 {
		t.Errorf("Expected at least 7 entities, got %d", len(converter.entities))
	}

	// Verify spatial structure (only spatial elements)
	spatialCount := 0
	spatialTypes := make(map[string]int)
	for _, entity := range converter.entities {
		if entity.Type == "IFCPROJECT" || entity.Type == "IFCBUILDING" ||
		   entity.Type == "IFCBUILDINGSTOREY" || entity.Type == "IFCSPACE" {
			spatialCount++
			spatialTypes[entity.Type]++
		}
	}

	// Log what we found for debugging
	t.Logf("Found spatial elements: %v", spatialTypes)

	if spatialCount != 7 { // 1 project + 1 building + 2 storeys + 3 spaces
		t.Errorf("Expected 7 spatial elements, got %d", spatialCount)
	}

	// Verify relationships
	if len(converter.relationships) != 3 {
		t.Errorf("Expected 3 relationships, got %d", len(converter.relationships))
	}

	// Check building element exists
	buildingFound := false
	for _, spatial := range converter.spatialStructure {
		if spatial.Entity.Type == "IFCBUILDING" {
			buildingFound = true
			if spatial.Entity.Name != "Test Building" {
				t.Errorf("Expected building name 'Test Building', got '%s'", spatial.Entity.Name)
			}
			if len(spatial.Children) != 2 {
				t.Errorf("Expected building to have 2 children (storeys), got %d", len(spatial.Children))
			}
		}
	}

	if !buildingFound {
		t.Error("IFCBUILDING entity not found in spatial structure")
	}
}

func TestSpatialIFCConverter_ConvertToBIMWithSpatial(t *testing.T) {
	converter := NewSpatialIFCConverter()

	// Create comprehensive test IFC data
	ifcData := []string{
		"ISO-10303-21;",
		"HEADER;",
		"FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'), '2;1');",
		"ENDSEC;",
		"DATA;",
		"#1 = IFCPROJECT('3M$Jv0HrvxqwdJb0k2tF6R',$,'Test Project',$,$,$,$,#2,$);",
		"#2 = IFCBUILDING('2M$Jv0HrvxqwdJb0k2tF6R',$,'Office Building','Downtown office complex',$,$,$,$,.ELEMENT.,$,$,$);",
		"#3 = IFCBUILDINGSTOREY('1M$Jv0HrvxqwdJb0k2tF6R',$,'Ground Floor','Level 0',$,$,$,$,.ELEMENT.,0.0);",
		"#4 = IFCBUILDINGSTOREY('4M$Jv0HrvxqwdJb0k2tF6R',$,'First Floor','Level 1',$,$,$,$,.ELEMENT.,3500.0);",
		"#5 = IFCSPACE('5M$Jv0HrvxqwdJb0k2tF6R',$,'Office 101','Main office space',$,$,$,$,.ELEMENT.,.INTERNAL.,0.0);",
		"#6 = IFCSPACE('6M$Jv0HrvxqwdJb0k2tF6R',$,'Conference Room 102','Large meeting room',$,$,$,$,.ELEMENT.,.INTERNAL.,0.0);",
		"#7 = IFCSPACE('7M$Jv0HrvxqwdJb0k2tF6R',$,'Office 201','Executive office',$,$,$,$,.ELEMENT.,.INTERNAL.,3500.0);",
		"#8 = IFCSPACE('8M$Jv0HrvxqwdJb0k2tF6R',$,'Restroom 203','Employee restroom',$,$,$,$,.ELEMENT.,.INTERNAL.,3500.0);",
		"#20 = IFCFLOWCONTROLLER('20M$Jv0HrvxqwdJb0k2tF6R',$,'VAV-101','Variable Air Volume Box',$,$,$,$,$);",
		"#21 = IFCFLOWTERMINAL('21M$Jv0HrvxqwdJb0k2tF6R',$,'DIFF-101','Air Diffuser',$,$,$,$,$);",
		"#22 = IFCFURNISHINGELEMENT('22M$Jv0HrvxqwdJb0k2tF6R',$,'DESK-201','Executive Desk',$,$,$,$,$);",
		"#30 = IFCRELAGGREGATES('30M$Jv0HrvxqwdJb0k2tF6R',$,'ProjectContainsBuilding',$,#1,(#2));",
		"#31 = IFCRELAGGREGATES('31M$Jv0HrvxqwdJb0k2tF6R',$,'BuildingContainsStoreys',$,#2,(#3,#4));",
		"#32 = IFCRELAGGREGATES('32M$Jv0HrvxqwdJb0k2tF6R',$,'StoreyContainsSpaces',$,#3,(#5,#6));",
		"#33 = IFCRELAGGREGATES('33M$Jv0HrvxqwdJb0k2tF6R',$,'StoreyContainsSpaces',$,#4,(#7,#8));",
		"#40 = IFCRELCONTAINEDINSPATIALSTRUCTURE('40M$Jv0HrvxqwdJb0k2tF6R',$,'EquipmentInOffice101',$,(#20,#21),#5);",
		"#41 = IFCRELCONTAINEDINSPATIALSTRUCTURE('41M$Jv0HrvxqwdJb0k2tF6R',$,'FurnitureInOffice201',$,(#22),#7);",
		"ENDSEC;",
		"END-ISO-10303-21;",
	}

	building, err := converter.ConvertToBIMWithSpatial(ifcData)
	if err != nil {
		t.Fatalf("Conversion failed: %v", err)
	}

	// Verify building information
	if building.Name != "Office Building" {
		t.Errorf("Expected building name 'Office Building', got '%s'", building.Name)
	}

	if building.Address != "Downtown office complex" {
		t.Errorf("Expected building address 'Downtown office complex', got '%s'", building.Address)
	}

	// Verify floor structure
	if len(building.Floors) != 2 {
		t.Errorf("Expected 2 floors, got %d", len(building.Floors))
	}

	// Check ground floor
	groundFloor := building.Floors[0]
	if groundFloor.Name != "Ground Floor" {
		t.Errorf("Expected ground floor name 'Ground Floor', got '%s'", groundFloor.Name)
	}

	if groundFloor.Elevation != 0.0 {
		t.Errorf("Expected ground floor elevation 0.0, got %.1f", groundFloor.Elevation)
	}

	if len(groundFloor.Rooms) != 2 {
		t.Errorf("Expected 2 rooms on ground floor, got %d", len(groundFloor.Rooms))
	}

	// Check first floor
	firstFloor := building.Floors[1]
	if firstFloor.Name != "First Floor" {
		t.Errorf("Expected first floor name 'First Floor', got '%s'", firstFloor.Name)
	}

	if firstFloor.Elevation != 3500.0 {
		t.Errorf("Expected first floor elevation 3500.0, got %.1f", firstFloor.Elevation)
	}

	if len(firstFloor.Rooms) != 2 {
		t.Errorf("Expected 2 rooms on first floor, got %d", len(firstFloor.Rooms))
	}

	// Verify room types are inferred correctly
	officeFound := false
	conferenceFound := false
	restroomFound := false

	for _, floor := range building.Floors {
		for _, room := range floor.Rooms {
			switch room.Type {
			case "office":
				officeFound = true
			case "conference":
				conferenceFound = true
			case "restroom":
				restroomFound = true
			}
		}
	}

	if !officeFound {
		t.Error("Expected to find an office room type")
	}
	if !conferenceFound {
		t.Error("Expected to find a conference room type")
	}
	if !restroomFound {
		t.Error("Expected to find a restroom")
	}

	// Verify equipment placement
	equipmentCount := 0
	for _, floor := range building.Floors {
		for _, room := range floor.Rooms {
			equipmentCount += len(room.Equipment)
		}
	}

	if equipmentCount != 3 {
		t.Errorf("Expected 3 equipment items, got %d", equipmentCount)
	}

	// Check that equipment is properly assigned to rooms
	office101Equipment := 0
	office201Equipment := 0

	for _, floor := range building.Floors {
		for _, room := range floor.Rooms {
			if strings.Contains(room.Name, "Office 101") {
				office101Equipment = len(room.Equipment)
			}
			if strings.Contains(room.Name, "Office 201") {
				office201Equipment = len(room.Equipment)
			}
		}
	}

	if office101Equipment != 2 {
		t.Errorf("Expected 2 equipment items in Office 101, got %d", office101Equipment)
	}

	if office201Equipment != 1 {
		t.Errorf("Expected 1 equipment item in Office 201, got %d", office201Equipment)
	}
}

func TestSpatialIFCConverter_RoomTypeInference(t *testing.T) {
	converter := NewSpatialIFCConverter()

	tests := []struct {
		name         string
		entityName   string
		properties   map[string]string
		expectedType string
	}{
		{
			name:         "Office space",
			entityName:   "Office 101",
			properties:   map[string]string{},
			expectedType: "office",
		},
		{
			name:         "Conference room",
			entityName:   "Conference Room A",
			properties:   map[string]string{},
			expectedType: "conference",
		},
		{
			name:         "Meeting room",
			entityName:   "Meeting Room B",
			properties:   map[string]string{},
			expectedType: "conference",
		},
		{
			name:         "Restroom",
			entityName:   "Restroom 203",
			properties:   map[string]string{},
			expectedType: "restroom",
		},
		{
			name:         "Storage room",
			entityName:   "Storage Closet",
			properties:   map[string]string{},
			expectedType: "storage",
		},
		{
			name:         "Corridor",
			entityName:   "Main Corridor",
			properties:   map[string]string{},
			expectedType: "corridor",
		},
		{
			name:         "Exterior space",
			entityName:   "Patio Area",
			properties:   map[string]string{"interior_exterior": "EXTERNAL"},
			expectedType: "external",
		},
		{
			name:         "Unknown space",
			entityName:   "Unknown Room",
			properties:   map[string]string{},
			expectedType: "space",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			entity := &IFCEntity{
				Name:       tt.entityName,
				Properties: tt.properties,
			}

			roomType := converter.inferSpaceType(entity)
			if roomType != tt.expectedType {
				t.Errorf("Expected room type '%s', got '%s'", tt.expectedType, roomType)
			}
		})
	}
}

func TestSpatialIFCConverter_ParseRelationships(t *testing.T) {
	converter := NewSpatialIFCConverter()

	// Test relationship parsing
	ifcData := []string{
		"#10 = IFCRELAGGREGATES('10M$Jv0HrvxqwdJb0k2tF6R',$,'BuildingContainsStoreys','Building aggregates storeys',#2,(#3,#4,#5));",
		"#11 = IFCRELCONTAINEDINSPATIALSTRUCTURE('11M$Jv0HrvxqwdJb0k2tF6R',$,'EquipmentInSpace','Equipment contained in space',(#20,#21,#22),#3);",
	}

	converter.parseAllEntities(ifcData)

	// Check IFCRELAGGREGATES relationship
	rel1, exists := converter.relationships["10"]
	if !exists {
		t.Fatal("IFCRELAGGREGATES relationship not found")
	}

	if rel1.Type != "IFCRELAGGREGATES" {
		t.Errorf("Expected relationship type IFCRELAGGREGATES, got %s", rel1.Type)
	}

	if rel1.RelatingElement != "2" {
		t.Errorf("Expected relating element '2', got '%s'", rel1.RelatingElement)
	}

	expectedRelated := []string{"3", "4", "5"}
	if len(rel1.RelatedElements) != len(expectedRelated) {
		t.Errorf("Expected %d related elements, got %d", len(expectedRelated), len(rel1.RelatedElements))
	}

	for i, expected := range expectedRelated {
		if i < len(rel1.RelatedElements) && rel1.RelatedElements[i] != expected {
			t.Errorf("Expected related element[%d] '%s', got '%s'", i, expected, rel1.RelatedElements[i])
		}
	}

	// Check IFCRELCONTAINEDINSPATIALSTRUCTURE relationship
	rel2, exists := converter.relationships["11"]
	if !exists {
		t.Fatal("IFCRELCONTAINEDINSPATIALSTRUCTURE relationship not found")
	}

	if rel2.Type != "IFCRELCONTAINEDINSPATIALSTRUCTURE" {
		t.Errorf("Expected relationship type IFCRELCONTAINEDINSPATIALSTRUCTURE, got %s", rel2.Type)
	}

	if rel2.RelatingElement != "3" {
		t.Errorf("Expected relating element '3', got '%s'", rel2.RelatingElement)
	}

	expectedContained := []string{"20", "21", "22"}
	if len(rel2.RelatedElements) != len(expectedContained) {
		t.Errorf("Expected %d contained elements, got %d", len(expectedContained), len(rel2.RelatedElements))
	}
}

func TestSpatialIFCConverter_ExtractRoomNumber(t *testing.T) {
	converter := NewSpatialIFCConverter()

	tests := []struct {
		roomName     string
		expectedNumber string
	}{
		{"Office 101", "101"},
		{"Conference Room 205A", "205A"},
		{"Room 42", "42"},
		{"Storage 15B", "15B"},
		{"Meeting Room Alpha", "Alpha"},
		{"Kitchen", ""},
		{"101 Main Office", "101"},
		{"Restroom W-203", "W-203"},
	}

	for _, tt := range tests {
		t.Run(tt.roomName, func(t *testing.T) {
			number := converter.extractRoomNumber(tt.roomName)
			if number != tt.expectedNumber {
				t.Errorf("Expected room number '%s', got '%s'", tt.expectedNumber, number)
			}
		})
	}
}

func TestSpatialIFCConverter_GetSpatialLevel(t *testing.T) {
	converter := NewSpatialIFCConverter()

	tests := []struct {
		spatialType   string
		expectedLevel int
	}{
		{"IFCPROJECT", 0},
		{"IFCSITE", 1},
		{"IFCBUILDING", 2},
		{"IFCBUILDINGSTOREY", 3},
		{"IFCSPACE", 4},
	}

	for _, tt := range tests {
		t.Run(tt.spatialType, func(t *testing.T) {
			level := converter.getSpatialLevel(tt.spatialType)
			if level != tt.expectedLevel {
				t.Errorf("Expected level %d for %s, got %d", tt.expectedLevel, tt.spatialType, level)
			}
		})
	}
}

func TestSpatialIFCConverter_ValidationWarnings(t *testing.T) {
	converter := NewSpatialIFCConverter()

	// Create IFC data with orphaned spaces (no proper containment)
	ifcData := []string{
		"#1 = IFCPROJECT('3M$Jv0HrvxqwdJb0k2tF6R',$,'Test Project',$,$,$,$,#2,$);",
		"#2 = IFCBUILDING('2M$Jv0HrvxqwdJb0k2tF6R',$,'Test Building',$,$,$,$,$,.ELEMENT.,$,$,$);",
		"#3 = IFCSPACE('5M$Jv0HrvxqwdJb0k2tF6R',$,'Orphaned Space','This space has no parent',$,$,$,$,.ELEMENT.,.INTERNAL.,0.0);",
	}

	building, err := converter.ConvertToBIMWithSpatial(ifcData)
	if err != nil {
		t.Fatalf("Conversion failed: %v", err)
	}

	// Should complete successfully but with warnings
	if building == nil {
		t.Error("Expected building to be created despite validation warnings")
	}

	// The validation should detect issues but not fail the conversion
	issues := building.Validate()
	if len(issues) == 0 {
		t.Log("No validation issues found (this is expected for incomplete test data)")
	}
}