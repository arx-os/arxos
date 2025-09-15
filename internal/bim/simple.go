package bim

// SimpleBIM is a simpler BIM structure for the unified platform
// This is used for quick conversion between database models and BIM format

// SimpleBuilding represents a simplified BIM building
type SimpleBuilding struct {
	Name      string                 `json:"name"`
	UUID      string                 `json:"uuid"`
	Version   string                 `json:"version"`
	Equipment []SimpleEquipment      `json:"equipment"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// SimpleEquipment represents simplified equipment in BIM
type SimpleEquipment struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	Path       string                 `json:"path,omitempty"`
	Status     string                 `json:"status"`
	Extensions map[string]interface{} `json:"extensions,omitempty"`
}

// NewSimpleBuilding creates a new simple building
func NewSimpleBuilding(name, uuid string) *SimpleBuilding {
	return &SimpleBuilding{
		Name:      name,
		UUID:      uuid,
		Version:   "2.0",
		Equipment: []SimpleEquipment{},
		Metadata:  make(map[string]interface{}),
	}
}

// AddEquipment adds equipment to the building
func (b *SimpleBuilding) AddEquipment(id, eqType, path, status string) {
	b.Equipment = append(b.Equipment, SimpleEquipment{
		ID:     id,
		Type:   eqType,
		Path:   path,
		Status: status,
	})
}

// SetIntelligence adds intelligence data to equipment
func (b *SimpleBuilding) SetIntelligence(equipmentID string, data map[string]interface{}) {
	for i := range b.Equipment {
		if b.Equipment[i].ID == equipmentID {
			if b.Equipment[i].Extensions == nil {
				b.Equipment[i].Extensions = make(map[string]interface{})
			}
			b.Equipment[i].Extensions["intelligence"] = data
			break
		}
	}
}

// SetSimulationResults adds simulation results to metadata
func (b *SimpleBuilding) SetSimulationResults(results map[string]interface{}) {
	b.Metadata["simulation_results"] = results
}