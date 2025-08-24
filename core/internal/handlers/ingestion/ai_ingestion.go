package ingestion

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

)

// AIIngestionHandler handles AI-powered floor plan processing
type AIIngestionHandler struct {
	openAIKey string
	db        interface{} // Will be *sql.DB when database is connected
}

// NewAIIngestionHandler creates a new AI ingestion handler
func NewAIIngestionHandler() *AIIngestionHandler {
	return &AIIngestionHandler{
		openAIKey: os.Getenv("OPENAI_API_KEY"),
	}
}

// AIIngestionRequest represents the incoming request
type AIIngestionRequest struct {
	Image    string `json:"image"`    // Base64 encoded image
	Filename string `json:"filename"`
	Prompt   string `json:"prompt"`
	Provider string `json:"provider"` // "openai", "google", "azure"
	Model    string `json:"model"`    // Specific model to use
}

// AIIngestionResponse represents the response
type AIIngestionResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data"`
	Error   string      `json:"error,omitempty"`
}

// FloorPlanData represents extracted floor plan information
type FloorPlanData struct {
	Walls    []WallData    `json:"walls"`
	Rooms    []RoomData    `json:"rooms"`
	Openings []OpeningData `json:"openings"`
	Labels   []LabelData   `json:"labels"`
	Metadata Metadata      `json:"metadata"`
}

// WallData represents a wall
type WallData struct {
	ID        string  `json:"id"`
	X1        float64 `json:"x1"`
	Y1        float64 `json:"y1"`
	X2        float64 `json:"x2"`
	Y2        float64 `json:"y2"`
	Type      string  `json:"type"`      // exterior, interior, partition
	Thickness string  `json:"thickness"` // thin, standard, thick
}

// RoomData represents a room/space
type RoomData struct {
	ID       string      `json:"id"`
	Boundary [][]float64 `json:"boundary"`
	Label    string      `json:"label"`
	Type     string      `json:"type"`
	Area     float64     `json:"area"`
}

// OpeningData represents doors/windows
type OpeningData struct {
	ID        string  `json:"id"`
	X         float64 `json:"x"`
	Y         float64 `json:"y"`
	Type      string  `json:"type"` // door, window, opening
	Width     float64 `json:"width"`
	Direction string  `json:"direction,omitempty"`
}

// LabelData represents text labels
type LabelData struct {
	Text string  `json:"text"`
	X    float64 `json:"x"`
	Y    float64 `json:"y"`
	Type string  `json:"type"`
}

// Metadata represents image metadata
type Metadata struct {
	Scale       float64 `json:"scale"`
	Orientation string  `json:"orientation"`
	Floor       string  `json:"floor,omitempty"`
}

// ProcessImage handles the AI ingestion endpoint
func (h *AIIngestionHandler) ProcessImage(w http.ResponseWriter, r *http.Request) {
	// Set CORS headers
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	// Parse request
	var req AIIngestionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate API key
	if h.openAIKey == "" {
		h.sendError(w, "OpenAI API key not configured", http.StatusInternalServerError)
		return
	}

	// Process based on provider
	var result *FloorPlanData
	var err error

	switch req.Provider {
	case "openai":
		result, err = h.processWithOpenAI(req)
	case "google":
		h.sendError(w, "Google Document AI not yet implemented", http.StatusNotImplemented)
		return
	case "azure":
		h.sendError(w, "Azure Form Recognizer not yet implemented", http.StatusNotImplemented)
		return
	default:
		result, err = h.processWithOpenAI(req) // Default to OpenAI
	}

	if err != nil {
		h.sendError(w, fmt.Sprintf("Processing failed: %v", err), http.StatusInternalServerError)
		return
	}

	// Send success response
	h.sendSuccess(w, result)
}

// processWithOpenAI sends the image to OpenAI Vision API
func (h *AIIngestionHandler) processWithOpenAI(req AIIngestionRequest) (*FloorPlanData, error) {
	// Prepare OpenAI API request
	openAIReq := map[string]interface{}{
		"model": "gpt-4-vision-preview",
		"messages": []map[string]interface{}{
			{
				"role": "user",
				"content": []map[string]interface{}{
					{
						"type": "text",
						"text": req.Prompt,
					},
					{
						"type": "image_url",
						"image_url": map[string]string{
							"url": fmt.Sprintf("data:image/jpeg;base64,%s", req.Image),
						},
					},
				},
			},
		},
		"max_tokens": 4096,
	}

	// Convert to JSON
	jsonData, err := json.Marshal(openAIReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	httpReq, err := http.NewRequest("POST", "https://api.openai.com/v1/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", h.openAIKey))

	// Send request
	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("OpenAI API error: %s", string(body))
	}

	// Parse OpenAI response
	var openAIResp struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}

	if err := json.Unmarshal(body, &openAIResp); err != nil {
		return nil, fmt.Errorf("failed to parse OpenAI response: %w", err)
	}

	if len(openAIResp.Choices) == 0 {
		return nil, fmt.Errorf("no response from OpenAI")
	}

	// Parse the JSON content from the AI response
	var floorPlanData FloorPlanData
	content := openAIResp.Choices[0].Message.Content
	
	// Extract JSON from the response (AI might include explanation text)
	startIdx := bytes.IndexByte([]byte(content), '{')
	endIdx := bytes.LastIndexByte([]byte(content), '}')
	
	if startIdx >= 0 && endIdx > startIdx {
		jsonContent := content[startIdx : endIdx+1]
		if err := json.Unmarshal([]byte(jsonContent), &floorPlanData); err != nil {
			return nil, fmt.Errorf("failed to parse floor plan data: %w", err)
		}
	} else {
		return nil, fmt.Errorf("no valid JSON found in AI response")
	}

	return &floorPlanData, nil
}

// sendSuccess sends a success response
func (h *AIIngestionHandler) sendSuccess(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	
	resp := AIIngestionResponse{
		Success: true,
		Data:    data,
	}
	
	json.NewEncoder(w).Encode(resp)
}

// sendError sends an error response
func (h *AIIngestionHandler) sendError(w http.ResponseWriter, message string, statusCode int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	
	resp := AIIngestionResponse{
		Success: false,
		Error:   message,
	}
	
	json.NewEncoder(w).Encode(resp)
}

// RegisterAIRoutes registers the AI ingestion routes using Chi
func RegisterAIRoutes(router interface{}) {
	handler := NewAIIngestionHandler()
	
	// Note: This function would need to be updated to work with Chi router
	// when integrated into the main routing setup
	_ = handler
}

// HealthCheck verifies AI service is available
func (h *AIIngestionHandler) HealthCheck(w http.ResponseWriter, r *http.Request) {
	status := map[string]interface{}{
		"service": "ai_ingestion",
		"status":  "healthy",
		"openai_configured": h.openAIKey != "",
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}