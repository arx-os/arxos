package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/arx-os/arxos/internal/domain/design"
)

// DesignUseCase implements design.DesignInterface
type DesignUseCase struct {
	componentService component.ComponentService
	// TODO: Add visual renderer, animation engine, etc.
}

// NewDesignUseCase creates a new design use case
func NewDesignUseCase(componentService component.ComponentService) design.DesignInterface {
	return &DesignUseCase{
		componentService: componentService,
	}
}

// CreateComponent creates a component through the design interface
func (uc *DesignUseCase) CreateComponent(ctx context.Context, req design.CreateComponentRequest) (*component.Component, error) {
	// Convert design request to component request
	componentReq := component.CreateComponentRequest{
		Name:       req.Name,
		Type:       req.Type,
		Path:       req.Path,
		Location:   req.Location,
		Properties: req.Properties,
		CreatedBy:  req.CreatedBy,
	}

	// Add visual style to properties if provided
	if req.VisualStyle != nil {
		if componentReq.Properties == nil {
			componentReq.Properties = make(map[string]any)
		}
		componentReq.Properties["visual_style"] = req.VisualStyle
	}

	// Create component
	comp, err := uc.componentService.CreateComponent(ctx, componentReq)
	if err != nil {
		return nil, fmt.Errorf("failed to create component: %w", err)
	}

	return comp, nil
}

// UpdateComponent updates a component through the design interface
func (uc *DesignUseCase) UpdateComponent(ctx context.Context, req design.UpdateComponentRequest) (*component.Component, error) {
	// Convert design request to component request
	componentReq := component.UpdateComponentRequest{
		ID:         req.ID,
		Name:       req.Name,
		Path:       req.Path,
		Location:   req.Location,
		Properties: req.Properties,
		UpdatedBy:  req.UpdatedBy,
	}

	// Add visual style to properties if provided
	if req.VisualStyle != nil {
		if componentReq.Properties == nil {
			componentReq.Properties = make(map[string]any)
		}
		componentReq.Properties["visual_style"] = req.VisualStyle
	}

	// Update component
	comp, err := uc.componentService.UpdateComponent(ctx, componentReq)
	if err != nil {
		return nil, fmt.Errorf("failed to update component: %w", err)
	}

	return comp, nil
}

// DeleteComponent deletes a component through the design interface
func (uc *DesignUseCase) DeleteComponent(ctx context.Context, componentID string) error {
	return uc.componentService.DeleteComponent(ctx, componentID)
}

// RenderComponent renders a component visually
func (uc *DesignUseCase) RenderComponent(ctx context.Context, componentID string) (*design.VisualRepresentation, error) {
	// Get component
	comp, err := uc.componentService.GetComponent(ctx, componentID)
	if err != nil {
		return nil, fmt.Errorf("component not found: %w", err)
	}

	// Create visual representation
	visual := &design.VisualRepresentation{
		ComponentID: comp.ID,
		Symbol:      uc.getComponentSymbol(comp.Type),
		Color:       uc.getComponentColor(comp.Type),
		Position: design.Position{
			X: int(comp.Location.X),
			Y: int(comp.Location.Y),
		},
		Size: design.Size{
			Width:  1,
			Height: 1,
		},
		Style: uc.getDefaultVisualStyle(comp.Type),
	}

	// Apply custom visual style if present
	if visualStyle, exists := comp.GetProperty("visual_style"); exists {
		if style, ok := visualStyle.(*design.VisualStyle); ok {
			visual.Style = *style
			visual.Symbol = style.Symbol
			visual.Color = style.Color
		}
	}

	return visual, nil
}

// RenderScene renders a complete scene
func (uc *DesignUseCase) RenderScene(ctx context.Context, filter component.ComponentFilter) (*design.Scene, error) {
	// Get components
	components, err := uc.componentService.ListComponents(ctx, filter)
	if err != nil {
		return nil, fmt.Errorf("failed to list components: %w", err)
	}

	// Create visual representations
	var visuals []design.VisualRepresentation
	for _, comp := range components {
		visual, err := uc.RenderComponent(ctx, comp.ID)
		if err != nil {
			continue // Skip components that can't be rendered
		}
		visuals = append(visuals, *visual)
	}

	// Create scene
	scene := &design.Scene{
		ID:         fmt.Sprintf("scene-%d", time.Now().Unix()),
		Name:       "Design Scene",
		Components: visuals,
		Viewport: design.Viewport{
			X:      0,
			Y:      0,
			Width:  80,
			Height: 24,
			Zoom:   1.0,
			Center: design.Position{X: 40, Y: 12},
		},
		Background: design.Background{
			Type:  design.BackgroundTypeSolid,
			Color: "black",
		},
		Grid: &design.Grid{
			Enabled: true,
			Size:    10,
			Color:   "gray",
			Style:   "dots",
		},
		CreatedAt: time.Now().Format(time.RFC3339),
		UpdatedAt: time.Now().Format(time.RFC3339),
	}

	return scene, nil
}

// SelectComponent selects a component for editing
func (uc *DesignUseCase) SelectComponent(ctx context.Context, componentID string) error {
	// TODO: Implement component selection logic
	// This would typically update the UI state to show the component as selected
	return nil
}

// MoveComponent moves a component to a new location
func (uc *DesignUseCase) MoveComponent(ctx context.Context, componentID string, newLocation component.Location) error {
	// Update component location
	req := component.UpdateComponentRequest{
		ID:        componentID,
		Location:  &newLocation,
		UpdatedBy: "design_interface",
	}

	_, err := uc.componentService.UpdateComponent(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to move component: %w", err)
	}

	return nil
}

// ConnectComponents connects two components
func (uc *DesignUseCase) ConnectComponents(ctx context.Context, sourceID, targetID string, relationType component.RelationType) error {
	req := component.AddRelationRequest{
		SourceComponentID: sourceID,
		RelationType:      relationType,
		TargetComponentID: targetID,
		CreatedBy:         "design_interface",
	}

	return uc.componentService.AddRelation(ctx, req)
}

// GetDesignTools returns available design tools
func (uc *DesignUseCase) GetDesignTools(ctx context.Context) ([]design.DesignTool, error) {
	tools := []design.DesignTool{
		{
			ID:          "create_component",
			Name:        "Create Component",
			Description: "Create a new building component",
			Category:    design.ToolCategoryCreate,
			Icon:        "➕",
			Enabled:     true,
		},
		{
			ID:          "move_component",
			Name:        "Move Component",
			Description: "Move a component to a new location",
			Category:    design.ToolCategoryModify,
			Icon:        "↔️",
			Enabled:     true,
		},
		{
			ID:          "connect_components",
			Name:        "Connect Components",
			Description: "Create a relationship between components",
			Category:    design.ToolCategoryConnect,
			Icon:        "🔗",
			Enabled:     true,
		},
		{
			ID:          "measure_distance",
			Name:        "Measure Distance",
			Description: "Measure distance between components",
			Category:    design.ToolCategoryMeasure,
			Icon:        "📏",
			Enabled:     true,
		},
		{
			ID:          "zoom_to_fit",
			Name:        "Zoom to Fit",
			Description: "Zoom viewport to fit all components",
			Category:    design.ToolCategoryView,
			Icon:        "🔍",
			Enabled:     true,
		},
	}

	return tools, nil
}

// UseDesignTool uses a design tool with parameters
func (uc *DesignUseCase) UseDesignTool(ctx context.Context, toolID string, params map[string]any) error {
	switch toolID {
	case "create_component":
		return uc.handleCreateComponentTool(ctx, params)
	case "move_component":
		return uc.handleMoveComponentTool(ctx, params)
	case "connect_components":
		return uc.handleConnectComponentsTool(ctx, params)
	case "zoom_to_fit":
		return uc.handleZoomToFitTool(ctx, params)
	default:
		return fmt.Errorf("unknown tool: %s", toolID)
	}
}

// SetViewport sets the current viewport
func (uc *DesignUseCase) SetViewport(ctx context.Context, viewport design.Viewport) error {
	// TODO: Implement viewport management
	return nil
}

// GetViewport gets the current viewport
func (uc *DesignUseCase) GetViewport(ctx context.Context) (*design.Viewport, error) {
	// TODO: Implement viewport management
	viewport := &design.Viewport{
		X:      0,
		Y:      0,
		Width:  80,
		Height: 24,
		Zoom:   1.0,
		Center: design.Position{X: 40, Y: 12},
	}
	return viewport, nil
}

// ZoomToComponent zooms the viewport to a specific component
func (uc *DesignUseCase) ZoomToComponent(ctx context.Context, componentID string) error {
	// TODO: Implement zoom to component
	return nil
}

// Undo undoes the last design action
func (uc *DesignUseCase) Undo(ctx context.Context) error {
	// TODO: Implement undo functionality
	return nil
}

// Redo redoes the last undone action
func (uc *DesignUseCase) Redo(ctx context.Context) error {
	// TODO: Implement redo functionality
	return nil
}

// GetHistory gets the design action history
func (uc *DesignUseCase) GetHistory(ctx context.Context) ([]design.DesignAction, error) {
	// TODO: Implement history tracking
	return []design.DesignAction{}, nil
}

// Helper methods

func (uc *DesignUseCase) getComponentSymbol(compType component.ComponentType) string {
	symbols := map[component.ComponentType]string{
		component.ComponentTypeHVACUnit:   "❄️",
		component.ComponentTypeDamper:     "🌪️",
		component.ComponentTypeThermostat: "🌡️",
		component.ComponentTypeVent:       "💨",
		component.ComponentTypePanel:      "⚡",
		component.ComponentTypeOutlet:     "🔌",
		component.ComponentTypeSwitch:     "🔘",
		component.ComponentTypeLight:      "💡",
		component.ComponentTypeFaucet:     "🚰",
		component.ComponentTypeToilet:     "🚽",
		component.ComponentTypePipe:       "🔧",
		component.ComponentTypeValve:      "🔩",
		component.ComponentTypeDetector:   "🚨",
		component.ComponentTypeSprinkler:  "💧",
		component.ComponentTypeAlarm:      "🔔",
		component.ComponentTypeDoor:       "🚪",
		component.ComponentTypeLock:       "🔒",
		component.ComponentTypeCardReader: "💳",
		component.ComponentTypeGeneric:    "📦",
		component.ComponentTypeFood:       "🍽️",
		component.ComponentTypeFurniture:  "🪑",
		component.ComponentTypeEquipment:  "⚙️",
	}

	if symbol, exists := symbols[compType]; exists {
		return symbol
	}
	return "📦" // Default symbol
}

func (uc *DesignUseCase) getComponentColor(compType component.ComponentType) string {
	colors := map[component.ComponentType]string{
		component.ComponentTypeHVACUnit:   "blue",
		component.ComponentTypeDamper:     "cyan",
		component.ComponentTypeThermostat: "yellow",
		component.ComponentTypeVent:       "white",
		component.ComponentTypePanel:      "red",
		component.ComponentTypeOutlet:     "green",
		component.ComponentTypeSwitch:     "yellow",
		component.ComponentTypeLight:      "yellow",
		component.ComponentTypeFaucet:     "blue",
		component.ComponentTypeToilet:     "white",
		component.ComponentTypePipe:       "gray",
		component.ComponentTypeValve:      "gray",
		component.ComponentTypeDetector:   "red",
		component.ComponentTypeSprinkler:  "blue",
		component.ComponentTypeAlarm:      "red",
		component.ComponentTypeDoor:       "brown",
		component.ComponentTypeLock:       "gray",
		component.ComponentTypeCardReader: "green",
		component.ComponentTypeGeneric:    "white",
		component.ComponentTypeFood:       "green",
		component.ComponentTypeFurniture:  "brown",
		component.ComponentTypeEquipment:  "gray",
	}

	if color, exists := colors[compType]; exists {
		return color
	}
	return "white" // Default color
}

func (uc *DesignUseCase) getDefaultVisualStyle(compType component.ComponentType) design.VisualStyle {
	return design.VisualStyle{
		Symbol:     uc.getComponentSymbol(compType),
		Color:      uc.getComponentColor(compType),
		Background: "black",
		Bold:       false,
		Italic:     false,
		Underline:  false,
		Blink:      false,
	}
}

// Tool handler methods

func (uc *DesignUseCase) handleCreateComponentTool(ctx context.Context, params map[string]any) error {
	// TODO: Implement create component tool
	return nil
}

func (uc *DesignUseCase) handleMoveComponentTool(ctx context.Context, params map[string]any) error {
	// TODO: Implement move component tool
	return nil
}

func (uc *DesignUseCase) handleConnectComponentsTool(ctx context.Context, params map[string]any) error {
	// TODO: Implement connect components tool
	return nil
}

func (uc *DesignUseCase) handleZoomToFitTool(ctx context.Context, params map[string]any) error {
	// TODO: Implement zoom to fit tool
	return nil
}
