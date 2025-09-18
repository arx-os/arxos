package output

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"
)

// Format represents the output format
type Format string

const (
	FormatText Format = "text"
	FormatJSON Format = "json"
)

// JSONWrapper wraps command output with metadata
type JSONWrapper struct {
	Success   bool        `json:"success"`
	Data      interface{} `json:"data,omitempty"`
	Error     string      `json:"error,omitempty"`
	Timestamp int64       `json:"timestamp"`
	Command   string      `json:"command,omitempty"`
	Version   string      `json:"version,omitempty"`
}

// Writer handles output formatting
type Writer struct {
	writer  io.Writer
	format  Format
	command string
}

// NewWriter creates a new output writer
func NewWriter(writer io.Writer, format Format, command string) *Writer {
	return &Writer{
		writer:  writer,
		format:  format,
		command: command,
	}
}

// WriteSuccess writes successful output
func (w *Writer) WriteSuccess(data interface{}) error {
	if w.format == FormatJSON {
		return w.writeJSON(true, data, "")
	}
	return w.writeText(data)
}

// WriteError writes error output
func (w *Writer) WriteError(err error) error {
	if w.format == FormatJSON {
		return w.writeJSON(false, nil, err.Error())
	}
	return w.writeTextError(err)
}

// writeJSON outputs data in JSON format with metadata
func (w *Writer) writeJSON(success bool, data interface{}, errorMsg string) error {
	wrapper := JSONWrapper{
		Success:   success,
		Data:      data,
		Timestamp: time.Now().Unix(),
		Command:   w.command,
		Version:   "1.0.0",
	}

	if errorMsg != "" {
		wrapper.Error = errorMsg
	}

	encoder := json.NewEncoder(w.writer)
	encoder.SetIndent("", "  ")
	return encoder.Encode(wrapper)
}

// writeText outputs data in human-readable text format
func (w *Writer) writeText(data interface{}) error {
	// For text output, we'll use the existing formatting logic
	// This is a simple implementation that can be extended
	_, err := fmt.Fprintln(w.writer, data)
	return err
}

// writeTextError outputs error in text format
func (w *Writer) writeTextError(err error) error {
	_, writeErr := fmt.Fprintf(w.writer, "Error: %v\n", err)
	return writeErr
}

// GetFormat determines output format from flags
func GetFormat(jsonFlag bool) Format {
	if jsonFlag {
		return FormatJSON
	}
	return FormatText
}

// Standard output helper
func WriteOutput(jsonFlag bool, command string, data interface{}) error {
	writer := NewWriter(os.Stdout, GetFormat(jsonFlag), command)
	return writer.WriteSuccess(data)
}

// Standard error helper
func WriteError(jsonFlag bool, command string, err error) error {
	writer := NewWriter(os.Stderr, GetFormat(jsonFlag), command)
	return writer.WriteError(err)
}

// Equipment list for JSON output
type EquipmentList struct {
	Equipment []EquipmentSummary `json:"equipment"`
	Total     int                `json:"total"`
}

// EquipmentSummary for JSON output
type EquipmentSummary struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Type     string `json:"type"`
	Status   string `json:"status"`
	RoomID   string `json:"room_id,omitempty"`
	Location *Point `json:"location,omitempty"`
	Notes    string `json:"notes,omitempty"`
}

// Point for location data
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// FloorPlanSummary for JSON output
type FloorPlanSummary struct {
	Name      string `json:"name"`
	Building  string `json:"building"`
	Level     int    `json:"level"`
	RoomCount int    `json:"room_count"`
	Equipment int    `json:"equipment_count"`
	FilePath  string `json:"file_path,omitempty"`
}

// StatusSummary for status command JSON output
type StatusSummary struct {
	FloorPlan        FloorPlanSummary   `json:"floor_plan"`
	EquipmentSummary map[string]int     `json:"equipment_summary"`
	FailedEquipment  []EquipmentSummary `json:"failed_equipment,omitempty"`
	NeedsRepair      []EquipmentSummary `json:"needs_repair,omitempty"`
	TotalEquipment   int                `json:"total_equipment"`
}

// TraceResult for trace command JSON output
type TraceResult struct {
	StartEquipment string      `json:"start_equipment"`
	Direction      string      `json:"direction"`
	MaxDepth       int         `json:"max_depth"`
	Results        []TraceStep `json:"results"`
	TotalFound     int         `json:"total_found"`
}

// TraceStep represents one step in a trace
type TraceStep struct {
	Level      int              `json:"level"`
	Equipment  EquipmentSummary `json:"equipment"`
	Connection string           `json:"connection_type,omitempty"`
}

// QueryResult for query command JSON output
type QueryResult struct {
	Columns []string        `json:"columns"`
	Rows    [][]interface{} `json:"rows"`
	Count   int             `json:"row_count"`
	Query   string          `json:"query"`
}

// ImportResult for import command JSON output
type ImportResult struct {
	SourceFile     string           `json:"source_file"`
	FloorPlan      FloorPlanSummary `json:"floor_plan"`
	StateFile      string           `json:"state_file"`
	ExtractionType string           `json:"extraction_type"` // "standard", "ocr", "manual"
	ProcessingTime float64          `json:"processing_time_ms"`
}

// ExportResult for export command JSON output
type ExportResult struct {
	SourceFloorPlan string `json:"source_floor_plan"`
	OutputFile      string `json:"output_file"`
	MarkupsSummary  struct {
		Failed      int `json:"failed_equipment"`
		NeedsRepair int `json:"needs_repair_equipment"`
		Total       int `json:"total_markups"`
	} `json:"markups_summary"`
	ProcessingTime float64 `json:"processing_time_ms"`
}

// ConnectionResult for connect/disconnect commands
type ConnectionResult struct {
	FromEquipment  string `json:"from_equipment"`
	ToEquipment    string `json:"to_equipment"`
	ConnectionType string `json:"connection_type"`
	Action         string `json:"action"` // "created", "removed"
}

// AnalysisResult for analyze command JSON output
type AnalysisResult struct {
	TargetEquipment    string             `json:"target_equipment"`
	DirectlyAffected   []EquipmentSummary `json:"directly_affected"`
	IndirectlyAffected []EquipmentSummary `json:"indirectly_affected"`
	TotalImpact        int                `json:"total_impact"`
	CriticalPath       bool               `json:"critical_path"`
	SystemsAffected    []string           `json:"systems_affected"`
	RiskLevel          string             `json:"risk_level"` // "low", "medium", "high", "critical"
}
