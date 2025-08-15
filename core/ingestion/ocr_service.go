// Package ingestion provides OCR services for extracting text from floor plans
package ingestion

import (
	"context"
	"encoding/json"
	"fmt"
	"image"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/otiai10/gosseract/v2"
)

// OCRService handles text extraction from images with room number detection
type OCRService struct {
	client      *gosseract.Client
	patterns    *TextPatterns
	cache       *OCRCache
	mu          sync.RWMutex
	config      OCRConfig
	metrics     OCRMetrics
}

// OCRConfig configures the OCR service
type OCRConfig struct {
	Language        string   `json:"language"`
	DPI            int      `json:"dpi"`
	PSM            int      `json:"psm"` // Page segmentation mode
	OEM            int      `json:"oem"` // OCR Engine mode
	Whitelist      string   `json:"whitelist"`
	EnableCache    bool     `json:"enable_cache"`
	CacheTTL       time.Duration `json:"cache_ttl"`
	MaxConcurrent  int      `json:"max_concurrent"`
	Confidence     float32  `json:"min_confidence"`
}

// OCRMetrics tracks OCR performance
type OCRMetrics struct {
	TotalExtractions  uint64
	SuccessfulReads   uint64
	FailedReads       uint64
	RoomNumbersFound  uint64
	AverageTimeMs     float64
	CacheHits         uint64
	CacheMisses       uint64
}

// ExtractedText represents OCR results
type ExtractedText struct {
	Text       string     `json:"text"`
	Confidence float32    `json:"confidence"`
	BoundingBox BBox      `json:"bounding_box"`
	TextType   TextType   `json:"type"`
	RoomInfo   *RoomInfo  `json:"room_info,omitempty"`
}

// RoomInfo contains parsed room information
type RoomInfo struct {
	Number      string   `json:"number"`
	Name        string   `json:"name,omitempty"`
	Type        string   `json:"type,omitempty"`
	Department  string   `json:"department,omitempty"`
	Capacity    int      `json:"capacity,omitempty"`
	Tags        []string `json:"tags,omitempty"`
}

// BBox represents a bounding box
type BBox struct {
	X      int `json:"x"`
	Y      int `json:"y"`
	Width  int `json:"width"`
	Height int `json:"height"`
}

// TextType categorizes extracted text
type TextType int

const (
	TextTypeUnknown TextType = iota
	TextTypeRoomNumber
	TextTypeRoomName
	TextTypeDoorLabel
	TextTypeEquipment
	TextTypeDimension
	TextTypeAnnotation
	TextTypeTitle
	TextTypeScale
)

// TextPatterns contains regex patterns for text classification
type TextPatterns struct {
	RoomNumber   *regexp.Regexp
	RoomName     *regexp.Regexp
	DoorLabel    *regexp.Regexp
	Equipment    *regexp.Regexp
	Dimension    *regexp.Regexp
	Scale        *regexp.Regexp
	Department   *regexp.Regexp
}

// NewOCRService creates a new OCR service instance
func NewOCRService(config OCRConfig) (*OCRService, error) {
	if config.MaxConcurrent == 0 {
		config.MaxConcurrent = 4
	}
	if config.Language == "" {
		config.Language = "eng"
	}
	if config.DPI == 0 {
		config.DPI = 300
	}
	if config.Confidence == 0 {
		config.Confidence = 60.0
	}

	client := gosseract.NewClient()
	client.SetLanguage(config.Language)
	
	if config.PSM > 0 {
		client.SetPageSegMode(gosseract.PageSegMode(config.PSM))
	}
	
	if config.Whitelist != "" {
		client.SetWhitelist(config.Whitelist)
	}

	service := &OCRService{
		client:   client,
		patterns: initializePatterns(),
		config:   config,
	}

	if config.EnableCache {
		service.cache = NewOCRCache(config.CacheTTL)
	}

	return service, nil
}

// ExtractFromImage processes an image and extracts text
func (s *OCRService) ExtractFromImage(ctx context.Context, img image.Image, region *BBox) ([]ExtractedText, error) {
	startTime := time.Now()
	defer func() {
		s.updateMetrics(time.Since(startTime))
	}()

	// Check cache if enabled
	if s.config.EnableCache && region != nil {
		cacheKey := fmt.Sprintf("%d_%d_%d_%d", region.X, region.Y, region.Width, region.Height)
		if cached, found := s.cache.Get(cacheKey); found {
			s.metrics.CacheHits++
			return cached, nil
		}
		s.metrics.CacheMisses++
	}

	// Apply region of interest if specified
	processImg := img
	if region != nil {
		processImg = cropImage(img, region)
	}

	// Set image for OCR
	s.client.SetImageFromBytes(imageToBytes(processImg))
	
	// Get detailed results with bounding boxes
	boxes, err := s.client.GetBoundingBoxes(gosseract.RIL_WORD)
	if err != nil {
		s.metrics.FailedReads++
		return nil, fmt.Errorf("OCR failed: %w", err)
	}

	// Process and classify extracted text
	results := make([]ExtractedText, 0, len(boxes))
	for _, box := range boxes {
		if box.Confidence < s.config.Confidence {
			continue
		}

		extracted := ExtractedText{
			Text:       box.Word,
			Confidence: box.Confidence,
			BoundingBox: BBox{
				X:      box.Box.Min.X,
				Y:      box.Box.Min.Y,
				Width:  box.Box.Max.X - box.Box.Min.X,
				Height: box.Box.Max.Y - box.Box.Min.Y,
			},
		}

		// Classify and enrich text
		s.classifyText(&extracted)
		
		// Parse room information if applicable
		if extracted.TextType == TextTypeRoomNumber {
			extracted.RoomInfo = s.parseRoomInfo(extracted.Text)
			s.metrics.RoomNumbersFound++
		}

		results = append(results, extracted)
	}

	// Group nearby text elements
	results = s.groupNearbyText(results)

	// Cache results if enabled
	if s.config.EnableCache && region != nil {
		cacheKey := fmt.Sprintf("%d_%d_%d_%d", region.X, region.Y, region.Width, region.Height)
		s.cache.Set(cacheKey, results)
	}

	s.metrics.SuccessfulReads++
	return results, nil
}

// ExtractRoomNumbers specifically extracts room numbers from an image
func (s *OCRService) ExtractRoomNumbers(ctx context.Context, img image.Image) ([]*RoomInfo, error) {
	texts, err := s.ExtractFromImage(ctx, img, nil)
	if err != nil {
		return nil, err
	}

	rooms := make([]*RoomInfo, 0)
	roomMap := make(map[string]*RoomInfo)

	// First pass: collect room numbers
	for _, text := range texts {
		if text.TextType == TextTypeRoomNumber && text.RoomInfo != nil {
			roomMap[text.RoomInfo.Number] = text.RoomInfo
		}
	}

	// Second pass: associate room names with numbers
	for _, text := range texts {
		if text.TextType == TextTypeRoomName {
			// Find nearest room number
			nearest := s.findNearestRoomNumber(text, texts)
			if nearest != nil && nearest.RoomInfo != nil {
				if room, exists := roomMap[nearest.RoomInfo.Number]; exists {
					room.Name = text.Text
				}
			}
		}
	}

	// Convert map to slice
	for _, room := range roomMap {
		rooms = append(rooms, room)
	}

	// Sort by room number
	sort.Slice(rooms, func(i, j int) bool {
		return rooms[i].Number < rooms[j].Number
	})

	return rooms, nil
}

// classifyText determines the type of extracted text
func (s *OCRService) classifyText(text *ExtractedText) {
	t := strings.TrimSpace(text.Text)
	
	// Check patterns in priority order
	if s.patterns.RoomNumber.MatchString(t) {
		text.TextType = TextTypeRoomNumber
	} else if s.patterns.Scale.MatchString(t) {
		text.TextType = TextTypeScale
	} else if s.patterns.Equipment.MatchString(t) {
		text.TextType = TextTypeEquipment
	} else if s.patterns.DoorLabel.MatchString(t) {
		text.TextType = TextTypeDoorLabel
	} else if s.patterns.Dimension.MatchString(t) {
		text.TextType = TextTypeDimension
	} else if len(t) > 10 && !strings.ContainsAny(t, "0123456789") {
		text.TextType = TextTypeRoomName
	} else {
		text.TextType = TextTypeUnknown
	}
}

// parseRoomInfo extracts structured room information
func (s *OCRService) parseRoomInfo(text string) *RoomInfo {
	info := &RoomInfo{
		Number: text,
		Tags:   make([]string, 0),
	}

	// Extract room type from number patterns
	upper := strings.ToUpper(text)
	switch {
	case strings.Contains(upper, "IDF"):
		info.Type = "IDF"
		info.Tags = append(info.Tags, "network", "infrastructure")
	case strings.Contains(upper, "MDF"):
		info.Type = "MDF"
		info.Tags = append(info.Tags, "network", "infrastructure", "main")
	case strings.Contains(upper, "ELEC"):
		info.Type = "Electrical"
		info.Tags = append(info.Tags, "electrical", "infrastructure")
	case strings.Contains(upper, "MECH"):
		info.Type = "Mechanical"
		info.Tags = append(info.Tags, "mechanical", "infrastructure")
	case strings.Contains(upper, "STOR"):
		info.Type = "Storage"
		info.Tags = append(info.Tags, "storage")
	case strings.Contains(upper, "CONF"):
		info.Type = "Conference"
		info.Tags = append(info.Tags, "meeting", "conference")
	case strings.Contains(upper, "LAB"):
		info.Type = "Laboratory"
		info.Tags = append(info.Tags, "lab", "research")
	default:
		// Try to detect office numbers
		if matched, _ := regexp.MatchString(`^\d{3,4}[A-Z]?$`, upper); matched {
			info.Type = "Office"
			info.Tags = append(info.Tags, "office")
		}
	}

	// Extract capacity from nearby text (would need context)
	// This would be enhanced with spatial analysis

	return info
}

// groupNearbyText groups text elements that are close together
func (s *OCRService) groupNearbyText(texts []ExtractedText) []ExtractedText {
	if len(texts) <= 1 {
		return texts
	}

	// Sort by Y position then X position
	sort.Slice(texts, func(i, j int) bool {
		if abs(texts[i].BoundingBox.Y-texts[j].BoundingBox.Y) < 10 {
			return texts[i].BoundingBox.X < texts[j].BoundingBox.X
		}
		return texts[i].BoundingBox.Y < texts[j].BoundingBox.Y
	})

	grouped := make([]ExtractedText, 0, len(texts))
	current := texts[0]
	
	for i := 1; i < len(texts); i++ {
		// Check if texts are on same line and close together
		if s.areNearby(current.BoundingBox, texts[i].BoundingBox) &&
		   current.TextType == texts[i].TextType {
			// Merge texts
			current.Text += " " + texts[i].Text
			current.BoundingBox = s.mergeBBoxes(current.BoundingBox, texts[i].BoundingBox)
			if texts[i].Confidence > current.Confidence {
				current.Confidence = texts[i].Confidence
			}
		} else {
			grouped = append(grouped, current)
			current = texts[i]
		}
	}
	grouped = append(grouped, current)

	return grouped
}

// findNearestRoomNumber finds the closest room number to a text element
func (s *OCRService) findNearestRoomNumber(target ExtractedText, texts []ExtractedText) *ExtractedText {
	var nearest *ExtractedText
	minDistance := float64(^uint(0) >> 1) // Max int

	for i := range texts {
		if texts[i].TextType != TextTypeRoomNumber {
			continue
		}

		dist := s.distance(target.BoundingBox, texts[i].BoundingBox)
		if dist < minDistance {
			minDistance = dist
			nearest = &texts[i]
		}
	}

	// Only return if reasonably close (within 100 pixels)
	if minDistance > 100 {
		return nil
	}

	return nearest
}

// Helper functions

func (s *OCRService) areNearby(b1, b2 BBox) bool {
	// Check if boxes are on approximately the same line
	if abs(b1.Y-b2.Y) > b1.Height/2 {
		return false
	}
	
	// Check horizontal distance
	gap := b2.X - (b1.X + b1.Width)
	return gap >= 0 && gap < b1.Height*2 // Within 2 character heights
}

func (s *OCRService) mergeBBoxes(b1, b2 BBox) BBox {
	minX := min(b1.X, b2.X)
	minY := min(b1.Y, b2.Y)
	maxX := max(b1.X+b1.Width, b2.X+b2.Width)
	maxY := max(b1.Y+b1.Height, b2.Y+b2.Height)
	
	return BBox{
		X:      minX,
		Y:      minY,
		Width:  maxX - minX,
		Height: maxY - minY,
	}
}

func (s *OCRService) distance(b1, b2 BBox) float64 {
	cx1 := float64(b1.X + b1.Width/2)
	cy1 := float64(b1.Y + b1.Height/2)
	cx2 := float64(b2.X + b2.Width/2)
	cy2 := float64(b2.Y + b2.Height/2)
	
	dx := cx1 - cx2
	dy := cy1 - cy2
	return math.Sqrt(dx*dx + dy*dy)
}

func (s *OCRService) updateMetrics(elapsed time.Duration) {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	s.metrics.TotalExtractions++
	
	// Update rolling average
	currentAvg := s.metrics.AverageTimeMs
	count := float64(s.metrics.TotalExtractions)
	s.metrics.AverageTimeMs = (currentAvg*(count-1) + float64(elapsed.Milliseconds())) / count
}

// Close cleans up OCR resources
func (s *OCRService) Close() error {
	if s.client != nil {
		s.client.Close()
	}
	if s.cache != nil {
		s.cache.Clear()
	}
	return nil
}

// GetMetrics returns current OCR metrics
func (s *OCRService) GetMetrics() OCRMetrics {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.metrics
}

// initializePatterns creates regex patterns for text classification
func initializePatterns() *TextPatterns {
	return &TextPatterns{
		// Room numbers: 101, 201A, B-205, IDF-1, MDF-2, etc.
		RoomNumber: regexp.MustCompile(`^[A-Z]*[-]?\d{2,4}[A-Z]?$|^(IDF|MDF|ELEC|MECH|STOR)[-]?\d*$`),
		
		// Room names: Conference Room, Lab, Office, etc.
		RoomName: regexp.MustCompile(`(?i)^(conference|meeting|lab|office|storage|mechanical|electrical|restroom|bathroom|kitchen|break\s*room)`),
		
		// Door labels: D1, D-101, EXIT, etc.
		DoorLabel: regexp.MustCompile(`^[D][-]?\d{1,3}$|^EXIT$|^ENTRANCE$`),
		
		// Equipment: VAV-1, AHU-2, PANEL-A, etc.
		Equipment: regexp.MustCompile(`^(VAV|AHU|FCU|RTU|PANEL|PDU|UPS)[-]?\w+$`),
		
		// Dimensions: 10'-6", 3.2m, 120 SF, etc.
		Dimension: regexp.MustCompile(`^\d+['-]\d*["']?$|^\d+\.?\d*\s*(m|ft|sf|sq\.?ft\.?)$`),
		
		// Scale: 1:100, 1/4" = 1', etc.
		Scale: regexp.MustCompile(`^1:\d+$|^\d+[/]\d+["']\s*=\s*\d+['"]$`),
		
		// Department: MATH, SCIENCE, ADMIN, etc.
		Department: regexp.MustCompile(`^(MATH|SCIENCE|ENGLISH|ADMIN|IT|HR|FINANCE|MAINTENANCE)$`),
	}
}

// OCRCache provides caching for OCR results
type OCRCache struct {
	cache map[string]cacheEntry
	ttl   time.Duration
	mu    sync.RWMutex
}

type cacheEntry struct {
	data      []ExtractedText
	timestamp time.Time
}

func NewOCRCache(ttl time.Duration) *OCRCache {
	cache := &OCRCache{
		cache: make(map[string]cacheEntry),
		ttl:   ttl,
	}
	
	// Start cleanup goroutine
	go cache.cleanup()
	
	return cache
}

func (c *OCRCache) Get(key string) ([]ExtractedText, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	entry, exists := c.cache[key]
	if !exists {
		return nil, false
	}
	
	if time.Since(entry.timestamp) > c.ttl {
		return nil, false
	}
	
	return entry.data, true
}

func (c *OCRCache) Set(key string, data []ExtractedText) {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	c.cache[key] = cacheEntry{
		data:      data,
		timestamp: time.Now(),
	}
}

func (c *OCRCache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.cache = make(map[string]cacheEntry)
}

func (c *OCRCache) cleanup() {
	ticker := time.NewTicker(c.ttl)
	defer ticker.Stop()
	
	for range ticker.C {
		c.mu.Lock()
		now := time.Now()
		for key, entry := range c.cache {
			if now.Sub(entry.timestamp) > c.ttl {
				delete(c.cache, key)
			}
		}
		c.mu.Unlock()
	}
}

// Utility functions
func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func cropImage(img image.Image, region *BBox) image.Image {
	// Implementation would crop the image to the specified region
	// This is a placeholder - actual implementation depends on image type
	return img
}

func imageToBytes(img image.Image) []byte {
	// Implementation would convert image to bytes for OCR
	// This is a placeholder - actual implementation depends on image format
	return []byte{}
}