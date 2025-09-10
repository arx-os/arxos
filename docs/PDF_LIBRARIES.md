# Go PDF Library Evaluation for ArxOS

## Requirements
- Extract text and coordinates from PDF floor plans
- Identify room labels and equipment markers
- Add markup layer to existing PDFs
- Export modified PDFs

## Library Options

### 1. pdfcpu (github.com/pdfcpu/pdfcpu)
**Pros:**
- Pure Go implementation
- Active development
- Good for basic PDF operations
- Can extract text with coordinates
- Supports annotations

**Cons:**
- Limited drawing capabilities
- Text extraction can be complex
- Documentation could be better

**Sample Usage:**
```go
import "github.com/pdfcpu/pdfcpu/pkg/api"

// Extract text
api.ExtractContentFile("floor.pdf", "output/", nil, nil)

// Add annotations
api.AddAnnotationsFile("floor.pdf", "marked.pdf", annotations, nil)
```

### 2. UniDoc (github.com/unidoc/unipdf)
**Pros:**
- Comprehensive PDF library
- Excellent text extraction with positioning
- Good drawing and annotation support
- Well documented

**Cons:**
- Commercial license required ($$$)
- Overkill for Phase 1 needs

### 3. gofpdf (github.com/jung-kurt/gofpdf)
**Pros:**
- Good for creating PDFs
- Simple API
- Pure Go

**Cons:**
- Cannot parse existing PDFs
- Only for generation, not reading

### 4. rsc.io/pdf
**Pros:**
- Simple PDF reader
- Lightweight
- By Russ Cox (Go team)

**Cons:**
- Read-only
- No modification capabilities
- Limited features

### 5. Hybrid Approach: pdfcpu + Custom Rendering
**Pros:**
- Use pdfcpu for extraction
- Custom code for text parsing
- Use pdfcpu for adding markup layer

**Cons:**
- More complex implementation
- Need to handle PDF coordinate systems

## Recommendation for Phase 1

**Use pdfcpu** with custom parsing logic:

1. **Text Extraction Phase:**
   - Use pdfcpu to extract text with coordinates
   - Parse room names and equipment labels
   - Build spatial map from coordinates

2. **ASCII Rendering Phase:**
   - Convert PDF coordinates to grid system
   - Generate ASCII art from spatial data

3. **Markup Export Phase:**
   - Use pdfcpu to add annotation layer
   - Overlay status markers on original PDF
   - Export combined PDF

## Implementation Plan

```go
// Step 1: Extract text elements
func ExtractFloorPlan(pdfPath string) (*models.FloorPlan, error) {
    // Extract all text with positions
    content, err := pdfcpu.ExtractContent(pdfPath)
    
    // Parse room labels (usually larger font)
    rooms := parseRooms(content)
    
    // Parse equipment (smaller font, specific patterns)
    equipment := parseEquipment(content)
    
    return &models.FloorPlan{
        Rooms: rooms,
        Equipment: equipment,
    }, nil
}

// Step 2: Add markups
func AddMarkups(pdfPath, outputPath string, markups []Markup) error {
    // Create annotations for each markup
    annotations := convertToAnnotations(markups)
    
    // Add to PDF
    return pdfcpu.AddAnnotations(pdfPath, outputPath, annotations)
}
```

## Next Steps

1. Install pdfcpu: `go get github.com/pdfcpu/pdfcpu/v3`
2. Create sample PDF with text elements
3. Test text extraction with coordinates
4. Build coordinate-to-grid mapping
5. Implement markup overlay

## Alternative for Complex PDFs

If PDF parsing proves too complex, consider:
- Requiring PDFs with text layers (not scanned images)
- Providing a template PDF format
- Using OCR service for scanned floor plans (Phase 2)
- Manual room/equipment mapping interface