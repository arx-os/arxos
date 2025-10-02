# ArxOS Intelligent Automation Strategy

## Overview

ArxOS implements **intelligent automation** across multiple layers to minimize manual object definition while maintaining user control and flexibility. The system uses AI, pattern recognition, and domain knowledge to automatically generate naming conventions, detect building components, and suggest configurations.

## 1. IFC-Based Automatic Detection

### A. Enhanced IFC Parsing with Intelligent Naming

```python
# services/ifcopenshell-service/models/intelligent_parser.py
class IntelligentIFCParser:
    """Enhanced IFC parser with automatic naming and classification"""
    
    def __init__(self):
        self.naming_patterns = {
            'building': {
                'office': ['office', 'tower', 'building', 'corporate'],
                'hospital': ['hospital', 'medical', 'clinic', 'health'],
                'school': ['school', 'university', 'college', 'education'],
                'residential': ['apartment', 'residential', 'housing', 'condo'],
                'industrial': ['factory', 'warehouse', 'industrial', 'manufacturing'],
                'retail': ['mall', 'retail', 'shopping', 'store']
            },
            'space': {
                'office': ['office', 'workstation', 'desk', 'cubicle'],
                'meeting': ['conference', 'meeting', 'boardroom', 'presentation'],
                'storage': ['storage', 'closet', 'archive', 'supply'],
                'mechanical': ['mechanical', 'electrical', 'utility', 'equipment'],
                'circulation': ['corridor', 'hallway', 'lobby', 'stair']
            },
            'equipment': {
                'hvac': ['ahu', 'chiller', 'boiler', 'pump', 'fan', 'vav'],
                'electrical': ['panel', 'transformer', 'generator', 'ups'],
                'plumbing': ['water_heater', 'pump', 'valve', 'fixture'],
                'fire': ['sprinkler', 'detector', 'alarm', 'extinguisher']
            }
        }
        
        self.property_extractors = {
            'name': self._extract_name,
            'description': self._extract_description,
            'classification': self._extract_classification,
            'properties': self._extract_properties,
            'materials': self._extract_materials,
            'spatial': self._extract_spatial_data
        }

    def parse_with_intelligence(self, ifc_data: bytes) -> IntelligentIFCResult:
        """Parse IFC with intelligent naming and classification"""
        result = IntelligentIFCResult()
        
        try:
            model = ifcopenshell.open(io.BytesIO(ifc_data))
            
            # Extract buildings with intelligent naming
            buildings = self._extract_buildings_intelligently(model)
            result.buildings = buildings
            
            # Extract spaces with automatic classification
            spaces = self._extract_spaces_intelligently(model)
            result.spaces = spaces
            
            # Extract equipment with automatic categorization
            equipment = self._extract_equipment_intelligently(model)
            result.equipment = equipment
            
            # Generate automatic naming suggestions
            result.naming_suggestions = self._generate_naming_suggestions(result)
            
            # Extract spatial relationships
            result.spatial_relationships = self._extract_spatial_relationships(model)
            
            # Generate repository structure suggestions
            result.structure_suggestions = self._generate_structure_suggestions(result)
            
        except Exception as e:
            result.errors.append(f"Intelligent parsing failed: {str(e)}")
            
        return result

    def _extract_buildings_intelligently(self, model) -> List[BuildingInfo]:
        """Extract buildings with intelligent naming and classification"""
        buildings = []
        
        for building in model.by_type('IfcBuilding'):
            building_info = BuildingInfo()
            
            # Extract basic info
            building_info.global_id = building.GlobalId
            building_info.name = building.Name or f"Building_{building.GlobalId[:8]}"
            building_info.description = building.Description or ""
            
            # Intelligent building type detection
            building_info.suggested_type = self._detect_building_type(
                building_info.name, 
                building_info.description
            )
            
            # Extract properties
            building_info.properties = self._extract_properties(building)
            
            # Extract spatial bounds
            building_info.bounds = self._extract_spatial_bounds(building)
            
            # Generate naming suggestions
            building_info.naming_suggestions = self._generate_building_names(building_info)
            
            buildings.append(building_info)
            
        return buildings

    def _detect_building_type(self, name: str, description: str) -> str:
        """Detect building type from name and description"""
        text = f"{name} {description}".lower()
        
        for building_type, keywords in self.naming_patterns['building'].items():
            if any(keyword in text for keyword in keywords):
                return building_type
                
        return 'office'  # Default fallback

    def _generate_building_names(self, building_info: BuildingInfo) -> List[str]:
        """Generate naming suggestions for buildings"""
        suggestions = []
        
        # Based on detected type
        type_suggestions = {
            'office': ['Corporate Office', 'Business Center', 'Office Tower'],
            'hospital': ['Medical Center', 'Hospital Complex', 'Healthcare Facility'],
            'school': ['Educational Campus', 'School Building', 'Learning Center'],
            'residential': ['Residential Complex', 'Apartment Building', 'Housing Development'],
            'industrial': ['Industrial Facility', 'Manufacturing Plant', 'Warehouse Complex'],
            'retail': ['Shopping Center', 'Retail Complex', 'Commercial Mall']
        }
        
        if building_info.suggested_type in type_suggestions:
            suggestions.extend(type_suggestions[building_info.suggested_type])
            
        # Based on location (if available)
        if building_info.properties.get('location'):
            location = building_info.properties['location']
            suggestions.append(f"{location} {building_info.suggested_type.title()}")
            
        # Based on size/scale
        if building_info.bounds:
            area = building_info.bounds.get('area', 0)
            if area > 10000:  # Large building
                suggestions.append(f"Major {building_info.suggested_type.title()} Complex")
            elif area > 5000:  # Medium building
                suggestions.append(f"{building_info.suggested_type.title()} Building")
            else:  # Small building
                suggestions.append(f"Small {building_info.suggested_type.title()}")
                
        return suggestions[:5]  # Return top 5 suggestions
```

### B. Automatic Space Classification

```python
def _extract_spaces_intelligently(self, model) -> List[SpaceInfo]:
    """Extract spaces with automatic classification and naming"""
    spaces = []
    
    for space in model.by_type('IfcSpace'):
        space_info = SpaceInfo()
        
        # Extract basic info
        space_info.global_id = space.GlobalId
        space_info.name = space.Name or f"Space_{space.GlobalId[:8]}"
        space_info.description = space.Description or ""
        
        # Intelligent space type detection
        space_info.suggested_type = self._detect_space_type(
            space_info.name, 
            space_info.description
        )
        
        # Extract spatial properties
        space_info.area = self._extract_area(space)
        space_info.volume = self._extract_volume(space)
        space_info.bounds = self._extract_spatial_bounds(space)
        
        # Generate naming suggestions
        space_info.naming_suggestions = self._generate_space_names(space_info)
        
        # Suggest floor assignment
        space_info.suggested_floor = self._detect_floor_level(space)
        
        spaces.append(space_info)
        
    return spaces

def _detect_space_type(self, name: str, description: str) -> str:
    """Detect space type from name and description"""
    text = f"{name} {description}".lower()
    
    for space_type, keywords in self.naming_patterns['space'].items():
        if any(keyword in text for keyword in keywords):
            return space_type
            
    # Additional intelligent detection based on properties
    if 'meeting' in text or 'conference' in text:
        return 'meeting'
    elif 'storage' in text or 'closet' in text:
        return 'storage'
    elif 'mechanical' in text or 'electrical' in text:
        return 'mechanical'
    elif 'corridor' in text or 'hallway' in text:
        return 'circulation'
    else:
        return 'office'  # Default fallback
```

## 2. Automatic Repository Structure Generation

### A. Intelligent Directory Structure

```go
// internal/infrastructure/filesystem/intelligent_structure.go
type IntelligentStructureGenerator struct {
    namingEngine *NamingEngine
    patterns     *NamingPatterns
}

type NamingEngine struct {
    buildingType    string
    floorCount      int
    detectedSpaces  []SpaceInfo
    detectedEquipment []EquipmentInfo
}

func (g *IntelligentStructureGenerator) GenerateStructure(repo *building.BuildingRepository, ifcResult *IntelligentIFCResult) (*RepositoryStructure, error) {
    structure := &RepositoryStructure{}
    
    // Generate IFC file naming
    structure.IFCFiles = g.generateIFCFileStructure(ifcResult)
    
    // Generate space-based directory structure
    structure.Spaces = g.generateSpaceStructure(ifcResult.Spaces)
    
    // Generate equipment-based structure
    structure.Equipment = g.generateEquipmentStructure(ifcResult.Equipment)
    
    // Generate operations structure based on building type
    structure.Operations = g.generateOperationsStructure(repo.Type, ifcResult)
    
    // Generate integration structure
    structure.Integrations = g.generateIntegrationStructure(repo.Type)
    
    return structure, nil
}

func (g *IntelligentStructureGenerator) generateIFCFileStructure(ifcResult *IntelligentIFCResult) []IFCFile {
    var ifcFiles []IFCFile
    
    for _, building := range ifcResult.Buildings {
        // Generate discipline-based naming
        disciplines := g.detectDisciplines(building)
        
        for _, discipline := range disciplines {
            ifcFile := IFCFile{
                ID:         generateUUID(),
                Name:       g.generateIFCFileName(building, discipline),
                Path:       g.generateIFCFilePath(building, discipline),
                Version:    "IFC4", // Detected from parsing
                Discipline: discipline,
                Size:       0, // Will be set when file is actually created
                Entities:   building.EntityCount,
                Validated:  true,
                CreatedAt:  time.Now(),
                UpdatedAt:  time.Now(),
            }
            ifcFiles = append(ifcFiles, ifcFile)
        }
    }
    
    return ifcFiles
}

func (g *IntelligentStructureGenerator) generateIFCFileName(building BuildingInfo, discipline string) string {
    // Generate intelligent file names
    baseName := g.sanitizeName(building.Name)
    
    // Add discipline suffix
    disciplineSuffix := map[string]string{
        "architectural": "arch",
        "structural":    "struct", 
        "mechanical":    "mech",
        "electrical":    "elec",
        "plumbing":      "plumb",
        "fire":          "fire",
    }
    
    suffix := disciplineSuffix[discipline]
    if suffix == "" {
        suffix = discipline[:4] // Use first 4 chars
    }
    
    return fmt.Sprintf("%s-%s-v1.ifc", baseName, suffix)
}

func (g *IntelligentStructureGenerator) generateSpaceStructure(spaces []SpaceInfo) []Space {
    var spaceStructures []Space
    
    // Group spaces by floor
    floorGroups := g.groupSpacesByFloor(spaces)
    
    for floor, floorSpaces := range floorGroups {
        for _, space := range floorSpaces {
            spaceStruct := Space{
                ID:          generateUUID(),
                Name:        space.Name,
                Type:        space.SuggestedType,
                Floor:       floor,
                Area:        space.Area,
                Volume:      space.Volume,
                Bounds:      space.Bounds,
                Properties:  space.Properties,
                CreatedAt:   time.Now(),
                UpdatedAt:   time.Now(),
            }
            spaceStructures = append(spaceStructures, spaceStruct)
        }
    }
    
    return spaceStructures
}
```

## 3. Automatic Equipment Detection and Categorization

### A. Equipment Intelligence Engine

```python
# services/ifcopenshell-service/models/equipment_intelligence.py
class EquipmentIntelligenceEngine:
    """Intelligent equipment detection and categorization"""
    
    def __init__(self):
        self.equipment_patterns = {
            'hvac': {
                'keywords': ['ahu', 'chiller', 'boiler', 'pump', 'fan', 'vav', 'duct', 'air'],
                'ifc_types': ['IfcAirTerminal', 'IfcFan', 'IfcPump', 'IfcBoiler', 'IfcChiller'],
                'naming_patterns': ['{type}_{location}_{capacity}', '{location}_{type}', '{type}_{id}']
            },
            'electrical': {
                'keywords': ['panel', 'transformer', 'generator', 'ups', 'electrical', 'power'],
                'ifc_types': ['IfcElectricDistributionBoard', 'IfcTransformer', 'IfcGenerator'],
                'naming_patterns': ['{type}_{floor}_{capacity}', '{location}_{type}', '{type}_{circuit}']
            },
            'plumbing': {
                'keywords': ['water', 'plumbing', 'fixture', 'valve', 'pipe', 'drain'],
                'ifc_types': ['IfcSanitaryTerminal', 'IfcValve', 'IfcPipeSegment'],
                'naming_patterns': ['{type}_{location}', '{location}_{type}', '{type}_{room}']
            },
            'fire': {
                'keywords': ['sprinkler', 'detector', 'alarm', 'fire', 'smoke', 'extinguisher'],
                'ifc_types': ['IfcFireSuppressionTerminal', 'IfcAlarm'],
                'naming_patterns': ['{type}_{zone}', '{zone}_{type}', '{type}_{room}']
            }
        }
        
        self.capacity_patterns = {
            'hvac': r'(\d+)\s*(ton|btu|cfm|kw|hp)',
            'electrical': r'(\d+)\s*(kw|kva|amp|volt)',
            'plumbing': r'(\d+)\s*(gpm|lpm|psi)',
            'fire': r'(\d+)\s*(gpm|psi|zone)'
        }

    def analyze_equipment(self, model) -> List[EquipmentInfo]:
        """Analyze equipment with intelligent categorization"""
        equipment_list = []
        
        # Analyze different equipment types
        for equipment_type, config in self.equipment_patterns.items():
            for ifc_type in config['ifc_types']:
                equipment_items = model.by_type(ifc_type)
                
                for item in equipment_items:
                    equipment_info = self._analyze_equipment_item(item, equipment_type)
                    if equipment_info:
                        equipment_list.append(equipment_info)
        
        return equipment_list

    def _analyze_equipment_item(self, item, category: str) -> EquipmentInfo:
        """Analyze individual equipment item"""
        equipment_info = EquipmentInfo()
        
        # Extract basic information
        equipment_info.global_id = item.GlobalId
        equipment_info.name = item.Name or f"{category}_{item.GlobalId[:8]}"
        equipment_info.description = item.Description or ""
        equipment_info.category = category
        
        # Extract properties
        equipment_info.properties = self._extract_equipment_properties(item)
        
        # Detect capacity/specifications
        equipment_info.specifications = self._extract_specifications(item, category)
        
        # Generate intelligent naming
        equipment_info.naming_suggestions = self._generate_equipment_names(equipment_info)
        
        # Detect location/room
        equipment_info.location = self._detect_equipment_location(item)
        
        # Suggest maintenance schedule
        equipment_info.maintenance_schedule = self._suggest_maintenance_schedule(equipment_info)
        
        return equipment_info

    def _generate_equipment_names(self, equipment: EquipmentInfo) -> List[str]:
        """Generate intelligent equipment naming suggestions"""
        suggestions = []
        
        # Get naming patterns for category
        patterns = self.equipment_patterns[equipment.category]['naming_patterns']
        
        for pattern in patterns:
            # Replace placeholders with actual values
            name = pattern.format(
                type=equipment.category.upper(),
                location=equipment.location or 'Unknown',
                capacity=equipment.specifications.get('capacity', ''),
                floor=equipment.location.split('_')[0] if '_' in equipment.location else '',
                room=equipment.location.split('_')[-1] if '_' in equipment.location else '',
                zone=equipment.properties.get('zone', ''),
                circuit=equipment.properties.get('circuit', ''),
                id=equipment.global_id[:8]
            )
            suggestions.append(name)
        
        # Add descriptive names based on properties
        if equipment.specifications.get('capacity'):
            capacity = equipment.specifications['capacity']
            suggestions.append(f"{equipment.category.title()} {capacity}")
        
        if equipment.location:
            suggestions.append(f"{equipment.location} {equipment.category.title()}")
        
        return suggestions[:5]  # Return top 5 suggestions
```

## 4. Automatic Configuration Generation

### A. Smart Configuration Engine

```go
// internal/infrastructure/config/intelligent_config.go
type IntelligentConfigGenerator struct {
    buildingType    string
    floorCount      int
    detectedSpaces  []SpaceInfo
    detectedEquipment []EquipmentInfo
}

func (g *IntelligentConfigGenerator) GenerateConfig(repo *building.BuildingRepository, ifcResult *IntelligentIFCResult) (*RepositoryConfig, error) {
    config := &RepositoryConfig{
        Repository: RepositoryConfigSection{
            ID:        repo.ID,
            Name:      repo.Name,
            Type:      string(repo.Type),
            Floors:    repo.Floors,
            CreatedAt: repo.CreatedAt,
            UpdatedAt: repo.UpdatedAt,
        },
        Structure: StructureConfigSection{
            Version: "1.0.0",
            Standard: "BUILDING_REPOSITORY_DESIGN.md",
        },
        Directories: g.generateDirectoryConfig(),
        Validation: g.generateValidationConfig(repo.Type),
        Import: g.generateImportConfig(repo.Type),
        Operations: g.generateOperationsConfig(repo.Type, ifcResult),
        Integrations: g.generateIntegrationConfig(repo.Type),
        Automation: g.generateAutomationConfig(repo.Type, ifcResult),
    }
    
    return config, nil
}

func (g *IntelligentConfigGenerator) generateOperationsConfig(buildingType string, ifcResult *IntelligentIFCResult) OperationsConfigSection {
    config := OperationsConfigSection{
        Maintenance: MaintenanceConfig{
            Enabled: true,
            AutoSchedule: true,
            WorkOrderTemplates: g.generateWorkOrderTemplates(buildingType),
            InspectionSchedules: g.generateInspectionSchedules(buildingType, ifcResult.Equipment),
        },
        Energy: EnergyConfig{
            Enabled: true,
            MonitoringPoints: g.generateEnergyMonitoringPoints(ifcResult.Equipment),
            OptimizationRules: g.generateEnergyOptimizationRules(buildingType),
        },
        Occupancy: OccupancyConfig{
            Enabled: true,
            SpaceUtilization: g.generateSpaceUtilizationConfig(ifcResult.Spaces),
            CapacityPlanning: g.generateCapacityPlanningConfig(ifcResult.Spaces),
        },
    }
    
    return config
}

func (g *IntelligentConfigGenerator) generateWorkOrderTemplates(buildingType string) []WorkOrderTemplate {
    templates := []WorkOrderTemplate{}
    
    // Generate templates based on building type
    switch buildingType {
    case "office":
        templates = append(templates, WorkOrderTemplate{
            Name: "HVAC Maintenance",
            Description: "Regular HVAC system maintenance",
            Frequency: "monthly",
            EquipmentTypes: []string{"hvac"},
            EstimatedDuration: "4 hours",
            RequiredSkills: []string{"hvac_technician"},
        })
        
    case "hospital":
        templates = append(templates, WorkOrderTemplate{
            Name: "Critical Systems Check",
            Description: "Critical hospital systems maintenance",
            Frequency: "weekly",
            EquipmentTypes: []string{"electrical", "hvac", "fire"},
            EstimatedDuration: "8 hours",
            RequiredSkills: []string{"electrical_technician", "hvac_technician"},
        })
        
    case "school":
        templates = append(templates, WorkOrderTemplate{
            Name: "Safety Systems Inspection",
            Description: "Safety systems inspection for educational facility",
            Frequency: "monthly",
            EquipmentTypes: []string{"fire", "electrical"},
            EstimatedDuration: "2 hours",
            RequiredSkills: []string{"fire_safety_technician"},
        })
    }
    
    return templates
}
```

## 5. User Override and Customization

### A. Intelligent Suggestions with User Control

```go
// internal/usecase/suggestion_usecase.go
type SuggestionUseCase struct {
    repoRepo    building.RepositoryRepository
    ifcRepo     building.IFCRepository
    logger      domain.Logger
}

func (uc *SuggestionUseCase) GenerateSuggestions(ctx context.Context, repoID string) (*SuggestionResult, error) {
    // Get repository
    repo, err := uc.repoRepo.GetByID(ctx, repoID)
    if err != nil {
        return nil, fmt.Errorf("failed to get repository: %w", err)
    }
    
    // Get IFC files
    ifcFiles, err := uc.ifcRepo.GetByRepository(ctx, repoID)
    if err != nil {
        return nil, fmt.Errorf("failed to get IFC files: %w", err)
    }
    
    result := &SuggestionResult{
        RepositoryID: repoID,
        Suggestions: []Suggestion{},
    }
    
    // Generate naming suggestions
    namingSuggestions := uc.generateNamingSuggestions(repo, ifcFiles)
    result.Suggestions = append(result.Suggestions, namingSuggestions...)
    
    // Generate structure suggestions
    structureSuggestions := uc.generateStructureSuggestions(repo, ifcFiles)
    result.Suggestions = append(result.Suggestions, structureSuggestions...)
    
    // Generate operation suggestions
    operationSuggestions := uc.generateOperationSuggestions(repo, ifcFiles)
    result.Suggestions = append(result.Suggestions, operationSuggestions...)
    
    return result, nil
}

func (uc *SuggestionUseCase) ApplySuggestion(ctx context.Context, repoID string, suggestionID string) error {
    // Get suggestion
    suggestion, err := uc.getSuggestion(suggestionID)
    if err != nil {
        return fmt.Errorf("failed to get suggestion: %w", err)
    }
    
    // Apply suggestion based on type
    switch suggestion.Type {
    case "naming":
        return uc.applyNamingSuggestion(ctx, repoID, suggestion)
    case "structure":
        return uc.applyStructureSuggestion(ctx, repoID, suggestion)
    case "operation":
        return uc.applyOperationSuggestion(ctx, repoID, suggestion)
    default:
        return fmt.Errorf("unknown suggestion type: %s", suggestion.Type)
    }
}
```

## 6. CLI Integration for Automation

### A. Automated Import with Suggestions

```bash
# User imports IFC file
arx import building.ifc --repository "Downtown Office Tower" --auto-suggest

# System automatically:
# 1. Parses IFC file with intelligent detection
# 2. Generates naming suggestions
# 3. Creates directory structure
# 4. Suggests equipment categorization
# 5. Generates operation templates
# 6. Creates integration configurations

# User can review and accept suggestions
arx suggestions --repository "Downtown Office Tower" --review
arx suggestions --repository "Downtown Office Tower" --apply suggestion-123
arx suggestions --repository "Downtown Office Tower" --customize suggestion-123
```

### B. Batch Processing

```bash
# Process multiple files with automation
arx batch-import data/ifc/*.ifc --repository "Downtown Office Tower" --auto-structure --auto-naming

# Generate suggestions for existing repository
arx suggest --repository "Downtown Office Tower" --type all --apply-auto
```

## 7. Benefits of This Automation Strategy

### **🤖 Intelligent Automation**
- **IFC Parsing**: Automatic detection of building types, spaces, and equipment
- **Naming Generation**: Context-aware naming suggestions based on content
- **Structure Creation**: Automatic directory and file organization
- **Configuration**: Smart defaults based on building type and detected components

### **🎯 User Control**
- **Override Capability**: Users can always override automatic suggestions
- **Customization**: Full customization of naming conventions and structures
- **Learning**: System learns from user preferences and corrections
- **Validation**: User validation of critical automated decisions

### **📈 Scalability**
- **Pattern Recognition**: Learns from similar buildings and projects
- **Template System**: Reusable templates for common building types
- **Batch Processing**: Efficient processing of multiple files
- **Integration**: Seamless integration with existing workflows

### **🛡️ Reliability**
- **Fallback Mechanisms**: Graceful degradation when automation fails
- **Validation**: Multiple validation layers for automated decisions
- **Audit Trail**: Complete audit trail of automated vs manual decisions
- **Error Handling**: Comprehensive error handling and recovery

This automation strategy significantly reduces manual work while maintaining user control and ensuring the system remains flexible and reliable.
