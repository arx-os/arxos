# ArxObject Symbol Library & Intelligent Ingestion System

## The Symbol Library - Teaching Arxos to Read Building Plans

### Overview
The Symbol Library is a comprehensive database of engineering symbols that the ingestion system uses to automatically identify and categorize objects in PDF/IFC files. Think of it as Arxos's "visual vocabulary" for understanding building plans.

## Symbol Library Structure

```go
type SystemSymbol struct {
    // Identity
    ID          string   // "symbol:electrical:outlet:duplex"
    System      string   // "electrical", "hvac", "plumbing", "fire", "structural"
    Category    string   // "outlet", "switch", "breaker", "fixture"
    SubType     string   // "duplex", "gfci", "dedicated", "weatherproof"
    
    // Visual Patterns (what to look for)
    Patterns    []Pattern {
        {
            Type: "circle_with_lines",  // Common outlet representation
            SVGPattern: "M0,0 A5,5 0 1,1 0,0.1 M-3,0 L3,0 M0,-3 L0,3",
            Confidence: 0.95,
        },
        {
            Type: "rectangle_with_slots",  // Alternative outlet style
            SVGPattern: "M0,0 L10,0 L10,5 L0,5 Z M3,2 L4,2 M6,2 L7,2",
            Confidence: 0.85,
        },
    }
    
    // Text Clues (labels to look for nearby)
    TextClues   []string {
        "DUPLEX",
        "120V",
        "20A",
        "GFCI",
        "WP",  // Weatherproof
    }
    
    // Properties to Auto-Assign
    DefaultProperties map[string]interface{} {
        "voltage": 120,
        "receptacles": 2,
        "mounting": "wall",
        "height_aff": 18,  // 18 inches above finished floor
    }
    
    // Common Sizes (for scale detection)
    TypicalSize struct {
        Width  float64  // 4.5 inches
        Height float64  // 2.75 inches
    }
    
    // Connection Rules
    ConnectionRules []ConnectionRule {
        {
            ExpectsConnection: "electrical_circuit",
            Direction: "upstream",
            Typical: "breaker_panel",
        },
    }
}
```

## System Symbol Libraries

### Electrical Symbol Library
```go
var ElectricalSymbols = []SystemSymbol{
    // Outlets
    {
        ID: "symbol:electrical:outlet:duplex",
        System: "electrical",
        Category: "outlet",
        SubType: "duplex",
        Patterns: []Pattern{
            {SVGPattern: "circle_with_two_lines"},
        },
        DefaultProperties: map[string]interface{}{
            "voltage": 120,
            "amperage": 20,
            "receptacles": 2,
        },
    },
    {
        ID: "symbol:electrical:outlet:gfci",
        System: "electrical",
        Category: "outlet",
        SubType: "gfci",
        Patterns: []Pattern{
            {SVGPattern: "circle_with_two_lines_and_g"},
        },
        TextClues: []string{"GFCI", "GFI"},
        DefaultProperties: map[string]interface{}{
            "voltage": 120,
            "amperage": 20,
            "gfci_protected": true,
        },
    },
    
    // Switches
    {
        ID: "symbol:electrical:switch:single_pole",
        System: "electrical",
        Category: "switch",
        SubType: "single_pole",
        Patterns: []Pattern{
            {SVGPattern: "circle_with_line_and_s"},
        },
        TextClues: []string{"SW", "S", "SP"},
    },
    
    // Lighting
    {
        ID: "symbol:electrical:light:recessed",
        System: "electrical",
        Category: "lighting",
        SubType: "recessed",
        Patterns: []Pattern{
            {SVGPattern: "circle_with_x_inside"},
        },
        TextClues: []string{"REC", "CAN", "DOWNLIGHT"},
    },
    
    // Panels
    {
        ID: "symbol:electrical:panel:distribution",
        System: "electrical",
        Category: "panel",
        SubType: "distribution",
        Patterns: []Pattern{
            {SVGPattern: "rectangle_with_grid"},
        },
        TextClues: []string{"PANEL", "PP", "LP", "42 CIRCUIT"},
    },
}
```

### HVAC Symbol Library
```go
var HVACSymbols = []SystemSymbol{
    {
        ID: "symbol:hvac:diffuser:supply",
        System: "hvac",
        Category: "diffuser",
        SubType: "supply",
        Patterns: []Pattern{
            {SVGPattern: "square_with_four_arrows_out"},
        },
        TextClues: []string{"SA", "SUPPLY", "CFM"},
        DefaultProperties: map[string]interface{}{
            "type": "supply",
            "shape": "square",
            "cfm": 100,
        },
    },
    {
        ID: "symbol:hvac:diffuser:return",
        System: "hvac",
        Category: "diffuser",
        SubType: "return",
        Patterns: []Pattern{
            {SVGPattern: "square_with_four_arrows_in"},
        },
        TextClues: []string{"RA", "RETURN", "CFM"},
    },
    {
        ID: "symbol:hvac:thermostat:wall",
        System: "hvac",
        Category: "control",
        SubType: "thermostat",
        Patterns: []Pattern{
            {SVGPattern: "circle_with_t"},
        },
        TextClues: []string{"TSTAT", "T", "THERMOSTAT"},
    },
}
```

### Plumbing Symbol Library
```go
var PlumbingSymbols = []SystemSymbol{
    {
        ID: "symbol:plumbing:fixture:toilet",
        System: "plumbing",
        Category: "fixture",
        SubType: "toilet",
        Patterns: []Pattern{
            {SVGPattern: "oval_with_rectangle"},
        },
        TextClues: []string{"WC", "TOILET", "LAV"},
        DefaultProperties: map[string]interface{}{
            "type": "floor_mounted",
            "gpf": 1.6,  // Gallons per flush
        },
    },
    {
        ID: "symbol:plumbing:fixture:sink",
        System: "plumbing",
        Category: "fixture",
        SubType: "sink",
        Patterns: []Pattern{
            {SVGPattern: "circle_or_rectangle"},
        },
        TextClues: []string{"SINK", "LAV", "S"},
    },
}
```

### Fire Protection Symbol Library
```go
var FireProtectionSymbols = []SystemSymbol{
    {
        ID: "symbol:fire:sprinkler:pendant",
        System: "fire_protection",
        Category: "sprinkler",
        SubType: "pendant",
        Patterns: []Pattern{
            {SVGPattern: "circle_with_cross"},
        },
        TextClues: []string{"SPRK", "SP", "PENDENT"},
        DefaultProperties: map[string]interface{}{
            "type": "pendant",
            "k_factor": 5.6,
            "temperature_rating": 155,
        },
    },
    {
        ID: "symbol:fire:alarm:pull_station",
        System: "fire_protection",
        Category: "alarm",
        SubType: "pull_station",
        Patterns: []Pattern{
            {SVGPattern: "square_with_fs"},
        },
        TextClues: []string{"PULL", "FS", "FIRE ALARM"},
    },
}
```

## Intelligent Ingestion Pipeline with Symbol Recognition

### Step 1: Symbol Library Loading
```go
func LoadSymbolLibraries() SymbolDatabase {
    db := SymbolDatabase{}
    
    // Load all system libraries
    db.Add(ElectricalSymbols...)
    db.Add(HVACSymbols...)
    db.Add(PlumbingSymbols...)
    db.Add(FireProtectionSymbols...)
    db.Add(StructuralSymbols...)
    
    // Build pattern matching index for fast lookup
    db.BuildPatternIndex()
    
    return db
}
```

### Step 2: PDF Ingestion with Symbol Recognition
```go
func IngestPDFWithSymbols(pdfFile []byte) ([]ArxObject, error) {
    // Load symbol library
    symbols := LoadSymbolLibraries()
    
    // Extract visual elements from PDF
    elements := ExtractPDFElements(pdfFile)
    
    arxObjects := []ArxObject{}
    
    for _, element := range elements {
        // Try to match against symbol library
        matches := symbols.FindMatches(element)
        
        if len(matches) > 0 {
            // Found a symbol match!
            bestMatch := matches[0]  // Highest confidence
            
            // Create ArxObject from symbol
            arxObj := ArxObject{
                ID:       GenerateID(),
                Type:     bestMatch.Category,
                SubType:  bestMatch.SubType,
                System:   bestMatch.System,
                Position: element.Position,
                Geometry: element.SVGPath,
                Properties: bestMatch.DefaultProperties,
                
                // Track what symbol was used
                Metadata: map[string]interface{}{
                    "symbol_id": bestMatch.ID,
                    "confidence": bestMatch.Confidence,
                    "recognized_by": "symbol_library",
                },
            }
            
            // Look for nearby text labels for additional properties
            nearbyText := FindNearbyText(element, elements)
            arxObj.Properties = EnrichWithTextClues(arxObj.Properties, nearbyText, bestMatch.TextClues)
            
            arxObjects = append(arxObjects, arxObj)
        }
    }
    
    return arxObjects, nil
}
```

### Step 3: Pattern Matching Algorithm
```go
func (db *SymbolDatabase) FindMatches(element PDFElement) []SymbolMatch {
    matches := []SymbolMatch{}
    
    for _, symbol := range db.Symbols {
        for _, pattern := range symbol.Patterns {
            similarity := CalculatePatternSimilarity(element.SVGPath, pattern.SVGPattern)
            
            if similarity > 0.8 {  // 80% match threshold
                matches = append(matches, SymbolMatch{
                    Symbol: symbol,
                    Confidence: similarity * pattern.Confidence,
                })
            }
        }
    }
    
    // Sort by confidence
    sort.Slice(matches, func(i, j int) bool {
        return matches[i].Confidence > matches[j].Confidence
    })
    
    return matches
}
```

### Step 4: Text Clue Enhancement
```go
func EnrichWithTextClues(properties map[string]interface{}, nearbyText []string, clues []string) map[string]interface{} {
    for _, text := range nearbyText {
        // Check for voltage specifications
        if matched, voltage := ExtractVoltage(text); matched {
            properties["voltage"] = voltage
        }
        
        // Check for amperage
        if matched, amps := ExtractAmperage(text); matched {
            properties["amperage"] = amps
        }
        
        // Check for circuit identification
        if matched, circuit := ExtractCircuit(text); matched {
            properties["circuit"] = circuit
        }
        
        // Check for specific clues
        for _, clue := range clues {
            if strings.Contains(strings.ToUpper(text), clue) {
                properties["label_text"] = text
                properties["matched_clue"] = clue
            }
        }
    }
    
    return properties
}
```

### Step 5: System-Specific Indexing
```go
func IndexBySystem(arxObjects []ArxObject) SystemIndex {
    index := SystemIndex{
        Electrical: []ArxObject{},
        HVAC:       []ArxObject{},
        Plumbing:   []ArxObject{},
        Fire:       []ArxObject{},
        Structural: []ArxObject{},
    }
    
    for _, obj := range arxObjects {
        switch obj.System {
        case "electrical":
            index.Electrical = append(index.Electrical, obj)
        case "hvac":
            index.HVAC = append(index.HVAC, obj)
        case "plumbing":
            index.Plumbing = append(index.Plumbing, obj)
        case "fire_protection":
            index.Fire = append(index.Fire, obj)
        case "structural":
            index.Structural = append(index.Structural, obj)
        }
    }
    
    return index
}
```

## Symbol Library Management

### Adding New Symbols (Community Contributions)
```go
func ContributeSymbol(newSymbol SystemSymbol, contributor User) (SystemSymbol, float64) {
    // Validate the symbol
    if ValidateSymbol(newSymbol) {
        // Add to pending library
        PendingSymbols.Add(newSymbol)
        
        // Calculate BILT reward
        biltReward := 10.0  // Base reward for new symbol
        
        if newSymbol.Patterns != nil {
            biltReward += 5.0  // Extra for pattern definition
        }
        
        if len(newSymbol.TextClues) > 3 {
            biltReward += 2.5  // Extra for comprehensive clues
        }
        
        // Award BILT to contributor
        contributor.EarnBILT(biltReward)
        
        return newSymbol, biltReward
    }
    
    return SystemSymbol{}, 0
}
```

### Symbol Library Versioning
```go
type SymbolLibraryVersion struct {
    Version     string
    ReleaseDate time.Time
    TotalSymbols int
    Systems     map[string]int  // Count per system
    Contributors []Contributor
    
    // Track changes
    NewSymbols     []SystemSymbol
    UpdatedSymbols []SystemSymbol
    DeprecatedSymbols []SystemSymbol
}
```

## Example: Complete Ingestion Flow

1. **User uploads electrical floor plan PDF**
2. **System loads Electrical Symbol Library**
3. **PDF parser extracts all visual elements**
4. **For each element:**
   - Compare against outlet patterns → "That's a duplex outlet!"
   - Check nearby text → "Says '20A GFCI'"
   - Create ArxObject with properties: `{voltage: 120, amperage: 20, gfci: true}`
   - Assign to electrical system index
5. **Connect related objects:**
   - Outlets connected to circuits
   - Circuits connected to panels
   - Panels connected to main distribution
6. **Generate SVGX with all recognized ArxObjects**
7. **Display in fractal viewer with system-colored layers**

## Benefits of Symbol Library Approach

1. **Consistency** - Same symbol always recognized the same way
2. **Speed** - Pre-defined patterns faster than AI inference
3. **Accuracy** - Engineering-specific patterns reduce false positives
4. **Extensibility** - Community can contribute new symbols
5. **System Organization** - Automatic categorization by engineering discipline
6. **BILT Rewards** - Contributors earn tokens for adding symbols
7. **Version Control** - Track symbol library evolution
8. **Industry Standards** - Can map to standard symbol libraries (IEEE, ANSI, etc.)

This Symbol Library is the "Rosetta Stone" that lets Arxos read any building plan and automatically understand what every symbol means, organizing them into the proper engineering systems.