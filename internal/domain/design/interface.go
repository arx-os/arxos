package design

import (
	"context"

	"github.com/arx-os/arxos/internal/domain/component"
)

// DesignInterface represents the universal CAD interface for any building component
type DesignInterface interface {
	// Component Management
	CreateComponent(ctx context.Context, req CreateComponentRequest) (*component.Component, error)
	UpdateComponent(ctx context.Context, req UpdateComponentRequest) (*component.Component, error)
	DeleteComponent(ctx context.Context, componentID string) error

	// Visual Design Operations
	RenderComponent(ctx context.Context, componentID string) (*VisualRepresentation, error)
	RenderScene(ctx context.Context, filter component.ComponentFilter) (*Scene, error)

	// Interactive Design Operations
	SelectComponent(ctx context.Context, componentID string) error
	MoveComponent(ctx context.Context, componentID string, newLocation component.Location) error
	ConnectComponents(ctx context.Context, sourceID, targetID string, relationType component.RelationType) error

	// Design Tools
	GetDesignTools(ctx context.Context) ([]DesignTool, error)
	UseDesignTool(ctx context.Context, toolID string, params map[string]any) error

	// Viewport Management
	SetViewport(ctx context.Context, viewport Viewport) error
	GetViewport(ctx context.Context) (*Viewport, error)
	ZoomToComponent(ctx context.Context, componentID string) error

	// Design History
	Undo(ctx context.Context) error
	Redo(ctx context.Context) error
	GetHistory(ctx context.Context) ([]DesignAction, error)
}

// CreateComponentRequest represents a request to create a component through the design interface
type CreateComponentRequest struct {
	Name        string                  `json:"name"`
	Type        component.ComponentType `json:"type"`
	Path        string                  `json:"path"`
	Location    component.Location      `json:"location"`
	Properties  map[string]any          `json:"properties"`
	VisualStyle *VisualStyle            `json:"visual_style,omitempty"`
	CreatedBy   string                  `json:"created_by"`
}

// UpdateComponentRequest represents a request to update a component through the design interface
type UpdateComponentRequest struct {
	ID          string              `json:"id"`
	Name        *string             `json:"name,omitempty"`
	Path        *string             `json:"path,omitempty"`
	Location    *component.Location `json:"location,omitempty"`
	Properties  map[string]any      `json:"properties,omitempty"`
	VisualStyle *VisualStyle        `json:"visual_style,omitempty"`
	UpdatedBy   string              `json:"updated_by"`
}

// VisualRepresentation represents how a component appears in the design interface
type VisualRepresentation struct {
	ComponentID string      `json:"component_id"`
	Symbol      string      `json:"symbol"`              // ASCII/Unicode symbol (e.g., "⚡", "🔧", "📦")
	Color       string      `json:"color"`               // Terminal color
	Position    Position    `json:"position"`            // Screen coordinates
	Size        Size        `json:"size"`                // Visual size
	Style       VisualStyle `json:"style"`               // Visual styling
	Animation   *Animation  `json:"animation,omitempty"` // Dynamic effects
}

// Scene represents a complete visual scene in the design interface
type Scene struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Components []VisualRepresentation `json:"components"`
	Viewport   Viewport               `json:"viewport"`
	Background Background             `json:"background"`
	Grid       *Grid                  `json:"grid,omitempty"`
	CreatedAt  string                 `json:"created_at"`
	UpdatedAt  string                 `json:"updated_at"`
}

// Position represents screen coordinates
type Position struct {
	X int `json:"x"`
	Y int `json:"y"`
}

// Size represents visual dimensions
type Size struct {
	Width  int `json:"width"`
	Height int `json:"height"`
}

// VisualStyle represents visual styling options
type VisualStyle struct {
	Symbol     string `json:"symbol"`
	Color      string `json:"color"`
	Background string `json:"background"`
	Bold       bool   `json:"bold"`
	Italic     bool   `json:"italic"`
	Underline  bool   `json:"underline"`
	Blink      bool   `json:"blink"`
}

// Animation represents dynamic visual effects
type Animation struct {
	Type       AnimationType  `json:"type"`
	Duration   int            `json:"duration"` // milliseconds
	Repeat     bool           `json:"repeat"`
	Properties map[string]any `json:"properties"`
}

// AnimationType represents types of animations
type AnimationType string

const (
	AnimationTypePulse    AnimationType = "pulse"
	AnimationTypeRotate   AnimationType = "rotate"
	AnimationTypeSlide    AnimationType = "slide"
	AnimationTypeFade     AnimationType = "fade"
	AnimationTypeParticle AnimationType = "particle"
	AnimationTypeFlow     AnimationType = "flow"
)

// Viewport represents the current view of the design interface
type Viewport struct {
	X      int      `json:"x"`
	Y      int      `json:"y"`
	Width  int      `json:"width"`
	Height int      `json:"height"`
	Zoom   float64  `json:"zoom"`
	Center Position `json:"center"`
}

// Background represents the scene background
type Background struct {
	Type    BackgroundType `json:"type"`
	Color   string         `json:"color"`
	Pattern string         `json:"pattern,omitempty"`
}

// BackgroundType represents background types
type BackgroundType string

const (
	BackgroundTypeSolid    BackgroundType = "solid"
	BackgroundTypePattern  BackgroundType = "pattern"
	BackgroundTypeGradient BackgroundType = "gradient"
)

// Grid represents a visual grid overlay
type Grid struct {
	Enabled bool   `json:"enabled"`
	Size    int    `json:"size"`
	Color   string `json:"color"`
	Style   string `json:"style"` // "dots", "lines", "crosses"
}

// DesignTool represents a tool available in the design interface
type DesignTool struct {
	ID          string         `json:"id"`
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Category    ToolCategory   `json:"category"`
	Icon        string         `json:"icon"`
	Parameters  map[string]any `json:"parameters"`
	Enabled     bool           `json:"enabled"`
}

// ToolCategory represents categories of design tools
type ToolCategory string

const (
	ToolCategoryCreate   ToolCategory = "create"
	ToolCategoryModify   ToolCategory = "modify"
	ToolCategoryConnect  ToolCategory = "connect"
	ToolCategoryMeasure  ToolCategory = "measure"
	ToolCategoryAnnotate ToolCategory = "annotate"
	ToolCategoryView     ToolCategory = "view"
	ToolCategoryUtility  ToolCategory = "utility"
)

// DesignAction represents an action in the design history
type DesignAction struct {
	ID          string         `json:"id"`
	Type        ActionType     `json:"type"`
	ComponentID string         `json:"component_id"`
	Data        map[string]any `json:"data"`
	Timestamp   string         `json:"timestamp"`
	User        string         `json:"user"`
}

// ActionType represents types of design actions
type ActionType string

const (
	ActionTypeCreate     ActionType = "create"
	ActionTypeUpdate     ActionType = "update"
	ActionTypeDelete     ActionType = "delete"
	ActionTypeMove       ActionType = "move"
	ActionTypeConnect    ActionType = "connect"
	ActionTypeDisconnect ActionType = "disconnect"
	ActionTypeStyle      ActionType = "style"
)
