package ifc

// Enhanced IFC data structures for full entity extraction
// These structures define what the IfcOpenShell service should return
// for complete Building/Floor/Room/Equipment extraction

// IFCBuildingEntity represents a parsed IFC Building
type IFCBuildingEntity struct {
	GlobalID    string                 `json:"global_id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description,omitempty"`
	LongName    string                 `json:"long_name,omitempty"`
	Address     *IFCAddress            `json:"address,omitempty"`
	Elevation   float64                `json:"elevation"`
	Properties  map[string]interface{} `json:"properties,omitempty"`
}

// IFCFloorEntity represents a parsed IFC BuildingStorey
type IFCFloorEntity struct {
	GlobalID    string                 `json:"global_id"`
	Name        string                 `json:"name"`
	LongName    string                 `json:"long_name,omitempty"`
	Description string                 `json:"description,omitempty"`
	Elevation   float64                `json:"elevation"`
	Height      float64                `json:"height,omitempty"`
	Properties  map[string]interface{} `json:"properties,omitempty"`
}

// IFCSpaceEntity represents a parsed IFC Space (Room)
type IFCSpaceEntity struct {
	GlobalID    string                 `json:"global_id"`
	Name        string                 `json:"name"`                // Room number
	LongName    string                 `json:"long_name,omitempty"` // Room name
	Description string                 `json:"description,omitempty"`
	FloorID     string                 `json:"floor_id"` // Parent floor GlobalID
	Placement   *IFCPlacement          `json:"placement,omitempty"`
	BoundingBox *IFCBoundingBox        `json:"bounding_box,omitempty"`
	Properties  map[string]interface{} `json:"properties,omitempty"`
}

// IFCEquipmentEntity represents a parsed IFC Product (Equipment)
type IFCEquipmentEntity struct {
	GlobalID       string           `json:"global_id"`
	Name           string           `json:"name"`
	Description    string           `json:"description,omitempty"`
	ObjectType     string           `json:"object_type"` // IfcFlowTerminal, IfcDistributionElement, etc.
	Tag            string           `json:"tag,omitempty"`
	SpaceID        string           `json:"space_id,omitempty"` // Parent space GlobalID
	Placement      *IFCPlacement    `json:"placement,omitempty"`
	Category       string           `json:"category,omitempty"` // electrical, hvac, plumbing, etc.
	PropertySets   []IFCPropertySet `json:"property_sets,omitempty"`
	Classification []string         `json:"classification,omitempty"`
}

// IFCAddress represents building address from IFC
type IFCAddress struct {
	AddressLines []string `json:"address_lines,omitempty"`
	PostalCode   string   `json:"postal_code,omitempty"`
	Town         string   `json:"town,omitempty"`
	Region       string   `json:"region,omitempty"`
	Country      string   `json:"country,omitempty"`
}

// IFCPlacement represents 3D placement/location
type IFCPlacement struct {
	X             float64   `json:"x"`
	Y             float64   `json:"y"`
	Z             float64   `json:"z"`
	RotationAxis  []float64 `json:"rotation_axis,omitempty"`
	RotationAngle float64   `json:"rotation_angle,omitempty"`
}

// IFCBoundingBox represents spatial bounds
type IFCBoundingBox struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MinZ float64 `json:"min_z"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
	MaxZ float64 `json:"max_z"`
}

// IFCPropertySet represents a property set (Pset)
type IFCPropertySet struct {
	Name       string                 `json:"name"`
	Properties map[string]interface{} `json:"properties"`
}

// IFCRelationship represents relationships between entities
type IFCRelationship struct {
	Type           string   `json:"type"`            // contains, connects, defines, etc.
	RelatingObject string   `json:"relating_object"` // GlobalID of source
	RelatedObjects []string `json:"related_objects"` // GlobalIDs of targets
	Description    string   `json:"description,omitempty"`
}

// EnhancedIFCResult represents the ENHANCED result we need from IFC parsing
// This is what the IfcOpenShell service should return for full entity extraction
type EnhancedIFCResult struct {
	// Backward compatible counts
	Success       bool        `json:"success"`
	Buildings     int         `json:"buildings"`
	Spaces        int         `json:"spaces"`
	Equipment     int         `json:"equipment"`
	Walls         int         `json:"walls"`
	Doors         int         `json:"doors"`
	Windows       int         `json:"windows"`
	TotalEntities int         `json:"total_entities"`
	Metadata      IFCMetadata `json:"metadata"`
	Error         *IFCError   `json:"error,omitempty"`

	// NEW: Detailed entity data for extraction
	BuildingEntities  []IFCBuildingEntity  `json:"building_entities,omitempty"`
	FloorEntities     []IFCFloorEntity     `json:"floor_entities,omitempty"`
	SpaceEntities     []IFCSpaceEntity     `json:"space_entities,omitempty"`
	EquipmentEntities []IFCEquipmentEntity `json:"equipment_entities,omitempty"`
	Relationships     []IFCRelationship    `json:"relationships,omitempty"`
}

// ConvertToEnhanced converts basic IFCResult to EnhancedIFCResult
// Used for backward compatibility when service doesn't return detailed entities yet
func (r *IFCResult) ConvertToEnhanced() *EnhancedIFCResult {
	return &EnhancedIFCResult{
		Success:           r.Success,
		Buildings:         r.Buildings,
		Spaces:            r.Spaces,
		Equipment:         r.Equipment,
		Walls:             r.Walls,
		Doors:             r.Doors,
		Windows:           r.Windows,
		TotalEntities:     r.TotalEntities,
		Metadata:          r.Metadata,
		Error:             r.Error,
		BuildingEntities:  []IFCBuildingEntity{},  // Empty for now
		FloorEntities:     []IFCFloorEntity{},     // Empty for now
		SpaceEntities:     []IFCSpaceEntity{},     // Empty for now
		EquipmentEntities: []IFCEquipmentEntity{}, // Empty for now
		Relationships:     []IFCRelationship{},    // Empty for now
	}
}
