package serialization

import (
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"gopkg.in/yaml.v3"
)

// EquipmentYAML represents equipment in YAML format for Git storage
// This follows the Kubernetes-style manifest format from the architecture doc
type EquipmentYAML struct {
	APIVersion  string               `yaml:"apiVersion"`
	Kind        string               `yaml:"kind"`
	Metadata    EquipmentMetadata    `yaml:"metadata"`
	Spec        EquipmentSpec        `yaml:"spec"`
	Status      EquipmentStatus      `yaml:"status"`
	Maintenance EquipmentMaintenance `yaml:"maintenance,omitempty"`
	ArxOS       ArxOSMetadata        `yaml:"_arxos"`
}

type EquipmentMetadata struct {
	Name        string            `yaml:"name"`
	Path        string            `yaml:"path"`
	ID          string            `yaml:"id"`
	Labels      map[string]string `yaml:"labels,omitempty"`
	Annotations map[string]string `yaml:"annotations,omitempty"`
}

type EquipmentSpec struct {
	Manufacturer string                 `yaml:"manufacturer,omitempty"`
	Model        string                 `yaml:"model,omitempty"`
	SerialNumber string                 `yaml:"serial_number,omitempty"`
	InstallDate  *time.Time             `yaml:"install_date,omitempty"`
	Capacity     map[string]interface{} `yaml:"capacity,omitempty"`
	Setpoints    map[string]float64     `yaml:"setpoints,omitempty"`
	Schedule     string                 `yaml:"schedule,omitempty"`
	Location     *LocationYAML          `yaml:"location,omitempty"`
	BAS          *BASConfig             `yaml:"bas,omitempty"`
}

type LocationYAML struct {
	X          float64 `yaml:"x"`
	Y          float64 `yaml:"y"`
	Z          float64 `yaml:"z"`
	ARAnchor   string  `yaml:"ar_anchor,omitempty"`
	Confidence float64 `yaml:"confidence,omitempty"`
	Source     string  `yaml:"source,omitempty"`
}

type BASConfig struct {
	System         string `yaml:"system,omitempty"`
	PointName      string `yaml:"point_name,omitempty"`
	NetworkAddress string `yaml:"network_address,omitempty"`
}

type EquipmentStatus struct {
	OperationalState string             `yaml:"operational_state"`
	Health           string             `yaml:"health"`
	CurrentValues    map[string]float64 `yaml:"current_values,omitempty"`
	Alarms           []Alarm            `yaml:"alarms,omitempty"`
	LastUpdated      time.Time          `yaml:"last_updated"`
}

type Alarm struct {
	Type         string    `yaml:"type"`
	Message      string    `yaml:"message"`
	Severity     string    `yaml:"severity"`
	Timestamp    time.Time `yaml:"timestamp"`
	Acknowledged bool      `yaml:"acknowledged"`
}

type EquipmentMaintenance struct {
	Schedule string     `yaml:"schedule,omitempty"`
	LastPM   *time.Time `yaml:"last_pm,omitempty"`
	NextPM   *time.Time `yaml:"next_pm,omitempty"`
	Vendor   string     `yaml:"vendor,omitempty"`
}

type ArxOSMetadata struct {
	PostGISID   string              `yaml:"postgis_id"`
	PostGISSync PostGISSyncMetadata `yaml:"postgis_sync"`
	GitCommit   string              `yaml:"git_commit,omitempty"`
}

type PostGISSyncMetadata struct {
	LastExport time.Time `yaml:"last_export"`
	LastImport time.Time `yaml:"last_import"`
}

// EquipmentToYAML converts a domain.Equipment to YAML format
func EquipmentToYAML(eq *domain.Equipment) (*EquipmentYAML, error) {
	yaml := &EquipmentYAML{
		APIVersion: "arxos.io/v1",
		Kind:       "Equipment",
		Metadata: EquipmentMetadata{
			Name:        eq.Name,
			Path:        eq.Path,
			ID:          eq.ID.String(),
			Labels:      buildLabels(eq),
			Annotations: buildAnnotations(eq),
		},
		Spec: EquipmentSpec{
			Manufacturer: eq.Model, // Using Model field for manufacturer for now
			Model:        eq.Model,
			Location:     convertLocation(eq.Location),
		},
		Status: EquipmentStatus{
			OperationalState: eq.Status,
			Health:           "healthy", // Default, would come from monitoring
			LastUpdated:      eq.UpdatedAt,
		},
		ArxOS: ArxOSMetadata{
			PostGISID: eq.ID.String(),
			PostGISSync: PostGISSyncMetadata{
				LastExport: time.Now(),
				LastImport: time.Now(),
			},
		},
	}

	return yaml, nil
}

// YAMLToEquipment converts YAML format to domain.Equipment
func YAMLToEquipment(yaml *EquipmentYAML) (*domain.Equipment, error) {
	eq := &domain.Equipment{
		Name:      yaml.Metadata.Name,
		Path:      yaml.Metadata.Path,
		Type:      yaml.Metadata.Labels["type"],
		Category:  yaml.Metadata.Labels["category"],
		Model:     yaml.Spec.Model,
		Status:    yaml.Status.OperationalState,
		UpdatedAt: yaml.Status.LastUpdated,
	}

	// Convert ID if present
	if yaml.Metadata.ID != "" {
		eq.ID = types.FromString(yaml.Metadata.ID)
	}

	// Convert location if present
	if yaml.Spec.Location != nil {
		eq.Location = &domain.Location{
			X: yaml.Spec.Location.X,
			Y: yaml.Spec.Location.Y,
			Z: yaml.Spec.Location.Z,
		}
	}

	return eq, nil
}

// MarshalEquipmentToYAML converts domain.Equipment to YAML bytes
func MarshalEquipmentToYAML(eq *domain.Equipment) ([]byte, error) {
	yamlData, err := EquipmentToYAML(eq)
	if err != nil {
		return nil, err
	}
	return yaml.Marshal(yamlData)
}

// UnmarshalEquipmentFromYAML converts YAML bytes to domain.Equipment
func UnmarshalEquipmentFromYAML(data []byte) (*domain.Equipment, error) {
	var yamlData EquipmentYAML
	if err := yaml.Unmarshal(data, &yamlData); err != nil {
		return nil, err
	}
	return YAMLToEquipment(&yamlData)
}

// Helper functions

func buildLabels(eq *domain.Equipment) map[string]string {
	labels := make(map[string]string)

	if eq.Type != "" {
		labels["type"] = eq.Type
	}
	if eq.Category != "" {
		labels["category"] = eq.Category
	}
	if eq.Subtype != "" {
		labels["subtype"] = eq.Subtype
	}

	// Add path-based labels
	if eq.Path != "" {
		pathParts := parsePath(eq.Path)
		if len(pathParts) >= 1 {
			labels["building"] = pathParts[0]
		}
		if len(pathParts) >= 2 {
			labels["floor"] = pathParts[1]
		}
		if len(pathParts) >= 3 {
			labels["room"] = pathParts[2]
		}
		if len(pathParts) >= 4 {
			labels["system"] = pathParts[3]
		}
	}

	return labels
}

func buildAnnotations(eq *domain.Equipment) map[string]string {
	annotations := make(map[string]string)

	if eq.CreatedAt.IsZero() {
		annotations["created_at"] = eq.CreatedAt.Format(time.RFC3339)
	}

	// Add any tags as annotations
	for i, tag := range eq.Tags {
		annotations[fmt.Sprintf("tag.%d", i)] = tag
	}

	return annotations
}

func convertLocation(loc *domain.Location) *LocationYAML {
	if loc == nil {
		return nil
	}

	return &LocationYAML{
		X: loc.X,
		Y: loc.Y,
		Z: loc.Z,
		// AR anchor and confidence would come from mobile scans
		Source: "ifc_import", // Default source
	}
}

func parsePath(path string) []string {
	// Remove leading slash and split by /
	if len(path) > 0 && path[0] == '/' {
		path = path[1:]
	}
	return strings.Split(path, "/")
}

// BuildingYAML represents building in YAML format for Git storage
type BuildingYAML struct {
	APIVersion string           `yaml:"apiVersion"`
	Kind       string           `yaml:"kind"`
	Metadata   BuildingMetadata `yaml:"metadata"`
	Spec       BuildingSpec     `yaml:"spec"`
	Status     BuildingStatus   `yaml:"status"`
}

type BuildingMetadata struct {
	Name        string            `yaml:"name"`
	ID          string            `yaml:"id"`
	Labels      map[string]string `yaml:"labels,omitempty"`
	Annotations map[string]string `yaml:"annotations,omitempty"`
	CreatedAt   time.Time         `yaml:"createdAt"`
	UpdatedAt   time.Time         `yaml:"updatedAt"`
}

type BuildingSpec struct {
	Address     string                 `yaml:"address"`
	Coordinates *LocationSpec          `yaml:"coordinates,omitempty"`
	Metadata    map[string]interface{} `yaml:"metadata,omitempty"`
}

type BuildingStatus struct {
	Phase string `yaml:"phase"`
}

type LocationSpec struct {
	X float64 `yaml:"x"`
	Y float64 `yaml:"y"`
	Z float64 `yaml:"z"`
}

// BuildingToYAML converts domain.Building to BuildingYAML
func BuildingToYAML(building *domain.Building) BuildingYAML {
	var coordinates *LocationSpec
	if building.Coordinates != nil {
		coordinates = &LocationSpec{
			X: building.Coordinates.X,
			Y: building.Coordinates.Y,
			Z: building.Coordinates.Z,
		}
	}

	return BuildingYAML{
		APIVersion: "arxos.io/v1",
		Kind:       "Building",
		Metadata: BuildingMetadata{
			Name:        building.Name,
			ID:          building.ID.String(),
			Labels:      make(map[string]string),
			Annotations: make(map[string]string),
			CreatedAt:   building.CreatedAt,
			UpdatedAt:   building.UpdatedAt,
		},
		Spec: BuildingSpec{
			Address:     building.Address,
			Coordinates: coordinates,
			Metadata:    make(map[string]interface{}),
		},
		Status: BuildingStatus{
			Phase: "Active",
		},
	}
}

// YAMLToBuilding converts BuildingYAML to domain.Building
func YAMLToBuilding(buildingYAML BuildingYAML) (*domain.Building, error) {
	id := types.FromString(buildingYAML.Metadata.ID)

	var coordinates *domain.Location
	if buildingYAML.Spec.Coordinates != nil {
		coordinates = &domain.Location{
			X: buildingYAML.Spec.Coordinates.X,
			Y: buildingYAML.Spec.Coordinates.Y,
			Z: buildingYAML.Spec.Coordinates.Z,
		}
	}

	return &domain.Building{
		ID:          id,
		Name:        buildingYAML.Metadata.Name,
		Address:     buildingYAML.Spec.Address,
		Coordinates: coordinates,
		CreatedAt:   buildingYAML.Metadata.CreatedAt,
		UpdatedAt:   buildingYAML.Metadata.UpdatedAt,
	}, nil
}

// MarshalBuildingToYAML marshals building to YAML bytes
func MarshalBuildingToYAML(building *domain.Building) ([]byte, error) {
	buildingYAML := BuildingToYAML(building)
	return yaml.Marshal(buildingYAML)
}

// UnmarshalBuildingFromYAML unmarshals building from YAML bytes
func UnmarshalBuildingFromYAML(data []byte) (*domain.Building, error) {
	var buildingYAML BuildingYAML
	if err := yaml.Unmarshal(data, &buildingYAML); err != nil {
		return nil, fmt.Errorf("failed to unmarshal building YAML: %w", err)
	}

	return YAMLToBuilding(buildingYAML)
}

// FloorYAML represents floor in YAML format for Git storage
type FloorYAML struct {
	APIVersion string        `yaml:"apiVersion"`
	Kind       string        `yaml:"kind"`
	Metadata   FloorMetadata `yaml:"metadata"`
	Spec       FloorSpec     `yaml:"spec"`
	Status     FloorStatus   `yaml:"status"`
}

type FloorMetadata struct {
	Name        string            `yaml:"name"`
	ID          string            `yaml:"id"`
	BuildingID  string            `yaml:"buildingId"`
	Labels      map[string]string `yaml:"labels,omitempty"`
	Annotations map[string]string `yaml:"annotations,omitempty"`
	CreatedAt   time.Time         `yaml:"createdAt"`
	UpdatedAt   time.Time         `yaml:"updatedAt"`
}

type FloorSpec struct {
	Level int `yaml:"level"`
}

type FloorStatus struct {
	Phase string `yaml:"phase"`
}

type BoundsSpec struct {
	MinX float64 `yaml:"minX"`
	MinY float64 `yaml:"minY"`
	MaxX float64 `yaml:"maxX"`
	MaxY float64 `yaml:"maxY"`
}

// FloorToYAML converts domain.Floor to FloorYAML
func FloorToYAML(floor *domain.Floor) FloorYAML {
	return FloorYAML{
		APIVersion: "arxos.io/v1",
		Kind:       "Floor",
		Metadata: FloorMetadata{
			Name:        floor.Name,
			ID:          floor.ID.String(),
			BuildingID:  floor.BuildingID.String(),
			Labels:      make(map[string]string),
			Annotations: make(map[string]string),
			CreatedAt:   floor.CreatedAt,
			UpdatedAt:   floor.UpdatedAt,
		},
		Spec: FloorSpec{
			Level: floor.Level,
		},
		Status: FloorStatus{
			Phase: "Active",
		},
	}
}

// YAMLToFloor converts FloorYAML to domain.Floor
func YAMLToFloor(floorYAML FloorYAML) (*domain.Floor, error) {
	id := types.FromString(floorYAML.Metadata.ID)
	buildingID := types.FromString(floorYAML.Metadata.BuildingID)

	return &domain.Floor{
		ID:         id,
		BuildingID: buildingID,
		Name:       floorYAML.Metadata.Name,
		Level:      floorYAML.Spec.Level,
		CreatedAt:  floorYAML.Metadata.CreatedAt,
		UpdatedAt:  floorYAML.Metadata.UpdatedAt,
	}, nil
}

// MarshalFloorToYAML marshals floor to YAML bytes
func MarshalFloorToYAML(floor *domain.Floor) ([]byte, error) {
	floorYAML := FloorToYAML(floor)
	return yaml.Marshal(floorYAML)
}

// UnmarshalFloorFromYAML unmarshals floor from YAML bytes
func UnmarshalFloorFromYAML(data []byte) (*domain.Floor, error) {
	var floorYAML FloorYAML
	if err := yaml.Unmarshal(data, &floorYAML); err != nil {
		return nil, fmt.Errorf("failed to unmarshal floor YAML: %w", err)
	}

	return YAMLToFloor(floorYAML)
}

// RoomYAML represents room in YAML format for Git storage
type RoomYAML struct {
	APIVersion string       `yaml:"apiVersion"`
	Kind       string       `yaml:"kind"`
	Metadata   RoomMetadata `yaml:"metadata"`
	Spec       RoomSpec     `yaml:"spec"`
	Status     RoomStatus   `yaml:"status"`
}

type RoomMetadata struct {
	Name        string            `yaml:"name"`
	ID          string            `yaml:"id"`
	FloorID     string            `yaml:"floorId"`
	Labels      map[string]string `yaml:"labels,omitempty"`
	Annotations map[string]string `yaml:"annotations,omitempty"`
	CreatedAt   time.Time         `yaml:"createdAt"`
	UpdatedAt   time.Time         `yaml:"updatedAt"`
}

type RoomSpec struct {
	Number   string                 `yaml:"number"`
	Location *LocationSpec          `yaml:"location,omitempty"`
	Width    float64                `yaml:"width,omitempty"`
	Height   float64                `yaml:"height,omitempty"`
	Metadata map[string]interface{} `yaml:"metadata,omitempty"`
}

type RoomStatus struct {
	Phase string `yaml:"phase"`
}

// RoomToYAML converts domain.Room to RoomYAML
func RoomToYAML(room *domain.Room) RoomYAML {
	var location *LocationSpec
	if room.Location != nil {
		location = &LocationSpec{
			X: room.Location.X,
			Y: room.Location.Y,
			Z: room.Location.Z,
		}
	}

	var metadata map[string]interface{}
	if room.Metadata != nil {
		if m, ok := room.Metadata.(map[string]interface{}); ok {
			metadata = m
		} else {
			metadata = make(map[string]interface{})
		}
	} else {
		metadata = make(map[string]interface{})
	}

	return RoomYAML{
		APIVersion: "arxos.io/v1",
		Kind:       "Room",
		Metadata: RoomMetadata{
			Name:        room.Name,
			ID:          room.ID.String(),
			FloorID:     room.FloorID.String(),
			Labels:      make(map[string]string),
			Annotations: make(map[string]string),
			CreatedAt:   room.CreatedAt,
			UpdatedAt:   room.UpdatedAt,
		},
		Spec: RoomSpec{
			Number:   room.Number,
			Location: location,
			Width:    room.Width,
			Height:   room.Height,
			Metadata: metadata,
		},
		Status: RoomStatus{
			Phase: "Active",
		},
	}
}

// YAMLToRoom converts RoomYAML to domain.Room
func YAMLToRoom(roomYAML RoomYAML) (*domain.Room, error) {
	id := types.FromString(roomYAML.Metadata.ID)
	floorID := types.FromString(roomYAML.Metadata.FloorID)

	var location *domain.Location
	if roomYAML.Spec.Location != nil {
		location = &domain.Location{
			X: roomYAML.Spec.Location.X,
			Y: roomYAML.Spec.Location.Y,
			Z: roomYAML.Spec.Location.Z,
		}
	}

	return &domain.Room{
		ID:        id,
		FloorID:   floorID,
		Name:      roomYAML.Metadata.Name,
		Number:    roomYAML.Spec.Number,
		Location:  location,
		Width:     roomYAML.Spec.Width,
		Height:    roomYAML.Spec.Height,
		Metadata:  roomYAML.Spec.Metadata,
		CreatedAt: roomYAML.Metadata.CreatedAt,
		UpdatedAt: roomYAML.Metadata.UpdatedAt,
	}, nil
}

// MarshalRoomToYAML marshals room to YAML bytes
func MarshalRoomToYAML(room *domain.Room) ([]byte, error) {
	roomYAML := RoomToYAML(room)
	return yaml.Marshal(roomYAML)
}

// UnmarshalRoomFromYAML unmarshals room from YAML bytes
func UnmarshalRoomFromYAML(data []byte) (*domain.Room, error) {
	var roomYAML RoomYAML
	if err := yaml.Unmarshal(data, &roomYAML); err != nil {
		return nil, fmt.Errorf("failed to unmarshal room YAML: %w", err)
	}

	return YAMLToRoom(roomYAML)
}
