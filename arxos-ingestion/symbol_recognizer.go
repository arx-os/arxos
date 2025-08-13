package ingestion

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
)

// SymbolRecognizer interfaces with the Python symbol recognition engine
type SymbolRecognizer struct {
	pythonPath string
	scriptPath string
}

// RecognitionRequest represents a request to recognize symbols
type RecognitionRequest struct {
	Content     []byte                 `json:"content"`
	ContentType string                 `json:"content_type"` // pdf, image, svg
	Options     map[string]interface{} `json:"options"`
}

// RecognitionResponse represents the response from symbol recognition
type RecognitionResponse struct {
	Symbols []RecognizedSymbolData `json:"symbols"`
	Errors  []string               `json:"errors"`
	Stats   RecognitionStats       `json:"stats"`
}

// RecognizedSymbolData represents a recognized symbol from Python
type RecognizedSymbolData struct {
	SymbolID    string                 `json:"symbol_id"`
	Confidence  float64                `json:"confidence"`
	MatchType   string                 `json:"match_type"`
	Position    map[string]float64     `json:"position"`
	SymbolData  map[string]interface{} `json:"symbol_data"`
	Context     string                 `json:"context"`
}

// RecognitionStats provides statistics about the recognition process
type RecognitionStats struct {
	TotalSymbols      int     `json:"total_symbols"`
	RecognizedSymbols int     `json:"recognized_symbols"`
	AverageConfidence float64 `json:"average_confidence"`
	ProcessingTime    float64 `json:"processing_time_ms"`
}

// NewSymbolRecognizer creates a new symbol recognizer
func NewSymbolRecognizer() (*SymbolRecognizer, error) {
	return &SymbolRecognizer{
		pythonPath: "python3",
		scriptPath: filepath.Join("services", "symbols", "recognize.py"),
	}, nil
}

// RecognizeInPDF recognizes symbols in a PDF document
func (r *SymbolRecognizer) RecognizeInPDF(pdfData []byte) (*RecognitionResponse, error) {
	request := RecognitionRequest{
		Content:     pdfData,
		ContentType: "pdf",
		Options: map[string]interface{}{
			"fuzzy_threshold": 0.6,
			"context_aware":   true,
		},
	}

	return r.callPythonRecognizer(request)
}

// RecognizeInImage recognizes symbols in an image (photo of paper map)
func (r *SymbolRecognizer) RecognizeInImage(imageData []byte) (*RecognitionResponse, error) {
	request := RecognitionRequest{
		Content:     imageData,
		ContentType: "image",
		Options: map[string]interface{}{
			"perspective_correction": true,
			"ocr_enabled":            true,
			"edge_detection":         true,
			"fuzzy_threshold":        0.5, // Lower threshold for photos
		},
	}

	return r.callPythonRecognizer(request)
}

// RecognizeInSVG recognizes symbols in SVG content
func (r *SymbolRecognizer) RecognizeInSVG(svgContent string) (*RecognitionResponse, error) {
	request := RecognitionRequest{
		Content:     []byte(svgContent),
		ContentType: "svg",
		Options: map[string]interface{}{
			"fuzzy_threshold": 0.7,
		},
	}

	return r.callPythonRecognizer(request)
}

// callPythonRecognizer calls the Python recognition script
func (r *SymbolRecognizer) callPythonRecognizer(request RecognitionRequest) (*RecognitionResponse, error) {
	// For now, we'll create a bridge script that interfaces with the existing Python code
	// In production, this would call the actual Python recognition engine
	
	// Create Python bridge script if it doesn't exist
	if err := r.ensurePythonBridge(); err != nil {
		return nil, fmt.Errorf("failed to ensure Python bridge: %w", err)
	}

	// Prepare request JSON
	requestJSON, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Call Python script
	cmd := exec.Command(r.pythonPath, r.scriptPath)
	cmd.Stdin = bytes.NewReader(requestJSON)
	
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to execute Python recognizer: %w", err)
	}

	// Parse response
	var response RecognitionResponse
	if err := json.Unmarshal(output, &response); err != nil {
		return nil, fmt.Errorf("failed to parse recognition response: %w", err)
	}

	return &response, nil
}

// ensurePythonBridge creates the Python bridge script if needed
func (r *SymbolRecognizer) ensurePythonBridge() error {
	// Check if the recognize.py script exists
	// If not, create it to bridge with the existing symbol_recognition.py
	
	bridgeScript := `#!/usr/bin/env python3
"""
Bridge script to interface with the existing symbol recognition engine.
Accepts JSON input via stdin and returns JSON output via stdout.
"""

import sys
import json
import base64
from io import BytesIO

# Add the services to path
sys.path.insert(0, '.')

from services.symbols.symbol_recognition import SymbolRecognitionEngine

def process_recognition_request():
    """Process a recognition request from Go."""
    try:
        # Read JSON request from stdin
        request_data = json.loads(sys.stdin.read())
        
        # Initialize recognition engine
        engine = SymbolRecognitionEngine()
        
        content_type = request_data.get('content_type', 'text')
        content = request_data.get('content', '')
        options = request_data.get('options', {})
        
        # Decode content if it's base64 encoded
        if isinstance(content, str) and content_type in ['pdf', 'image']:
            content = base64.b64decode(content)
        
        # Perform recognition based on content type
        if content_type == 'pdf':
            symbols = recognize_pdf(engine, content, options)
        elif content_type == 'image':
            symbols = recognize_image(engine, content, options)
        elif content_type == 'svg':
            symbols = engine.recognize_symbols_in_content(content, 'svg')
        else:
            symbols = engine.recognize_symbols_in_content(content, 'text')
        
        # Calculate statistics
        total_symbols = len(symbols)
        recognized_symbols = len([s for s in symbols if s.get('confidence', 0) > 0.5])
        avg_confidence = sum(s.get('confidence', 0) for s in symbols) / total_symbols if total_symbols > 0 else 0
        
        # Prepare response
        response = {
            'symbols': symbols,
            'errors': [],
            'stats': {
                'total_symbols': total_symbols,
                'recognized_symbols': recognized_symbols,
                'average_confidence': avg_confidence,
                'processing_time_ms': 0  # Would need timing logic
            }
        }
        
        print(json.dumps(response))
        
    except Exception as e:
        error_response = {
            'symbols': [],
            'errors': [str(e)],
            'stats': {
                'total_symbols': 0,
                'recognized_symbols': 0,
                'average_confidence': 0,
                'processing_time_ms': 0
            }
        }
        print(json.dumps(error_response))
        sys.exit(1)

def recognize_pdf(engine, pdf_content, options):
    """Recognize symbols in PDF content."""
    # This would use pdf2image or PyPDF2 to extract content
    # For now, return mock data
    return engine.fuzzy_match_symbols('outlet', options.get('fuzzy_threshold', 0.6))

def recognize_image(engine, image_content, options):
    """Recognize symbols in image content."""
    # This would use OpenCV for perspective correction and OCR
    # For now, return mock data
    return engine.fuzzy_match_symbols('door', options.get('fuzzy_threshold', 0.5))

if __name__ == '__main__':
    process_recognition_request()
`

	// Write the bridge script if needed
	// This is a simplified version - in production, the script would be more robust
	
	return nil
}

// ConvertPythonSymbol converts Python recognition data to Go structure
func (r *SymbolRecognizer) ConvertPythonSymbol(data RecognizedSymbolData) *RecognizedSymbol {
	symbol := &RecognizedSymbol{
		Definition: &SymbolDefinition{
			ID:         data.SymbolID,
			Properties: data.SymbolData,
		},
		Position: Position{
			X: data.Position["x"],
			Y: data.Position["y"],
			Z: data.Position["z"],
		},
		Confidence: data.Confidence,
		Context:    data.Context,
	}

	// Extract additional properties from symbol data
	if name, ok := data.SymbolData["display_name"].(string); ok {
		symbol.Definition.Name = name
		symbol.Definition.DisplayName = name
	}
	
	if system, ok := data.SymbolData["system"].(string); ok {
		symbol.Definition.System = system
	}
	
	if category, ok := data.SymbolData["category"].(string); ok {
		symbol.Definition.Category = category
	}
	
	if tags, ok := data.SymbolData["tags"].([]interface{}); ok {
		for _, tag := range tags {
			if tagStr, ok := tag.(string); ok {
				symbol.Definition.Tags = append(symbol.Definition.Tags, tagStr)
			}
		}
	}
	
	if svg, ok := data.SymbolData["svg"].(string); ok {
		symbol.Definition.SVG = svg
	}

	return symbol
}