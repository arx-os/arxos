# ASCII-BIM System: Complete Architecture & Implementation

## 🎯 **Overview**

The ASCII-BIM System provides comprehensive ASCII-BIM format processing capabilities for the Arxos platform, including parsing, rendering, validation, and conversion to/from SVGX format.

**Status**: 🔄 **IN DEVELOPMENT**
**Priority**: High

---

## 📊 **Current State Analysis**

### ✅ **What's Already Built**
- Export functionality (ASCII-BIM export in export_interoperability.py)
- Basic CLI integration (arx-cli with ASCII-BIM support)
- Format definition (ASCII-BIM as export format)
- API endpoints for ASCII-BIM export

### ❌ **What's Missing**
- Complete ASCII-BIM parser/reader
- ASCII-BIM to SVGX conversion
- ASCII-BIM editing capabilities
- ASCII-BIM validation system
- ASCII-BIM diff/merge functionality
- ASCII-BIM visualization tools

---

## 🏗️ **Complete Architecture Plan**

### **1.1 ASCII-BIM Core Engine**

```python
# arxos/svgx_engine/services/ascii_bim_engine.py
class ASCIIBIMEngine:
    """Complete ASCII-BIM processing engine"""

    def __init__(self):
        self.parser = ASCIIBIMParser()
        self.renderer = ASCIIBIMRenderer()
        self.validator = ASCIIBIMValidator()
        self.converter = ASCIIBIMConverter()

    async def parse_ascii_bim(self, content: str) -> ASCIIBIMModel:
        """Parse ASCII-BIM content into structured model"""

        # Validate input
        if not content or not content.strip():
            raise ValueError("Empty ASCII-BIM content")

        # Parse building structure
        building = await self.parser.parse_building_block(content)

        # Parse elements
        elements = await self.parser.parse_elements_block(content)

        # Parse systems
        systems = await self.parser.parse_systems_block(content)

        # Create structured model
        model = ASCIIBIMModel(
            building=building,
            elements=elements,
            systems=systems,
            metadata=self.extract_metadata(content)
        )

        return model

    async def render_ascii_bim(self, model: ASCIIBIMModel) -> str:
        """Render structured model to ASCII-BIM format"""

        # Validate model
        if not model:
            raise ValueError("Invalid ASCII-BIM model")

        # Render building section
        building_section = await self.renderer.render_building(model.building)

        # Render elements section
        elements_section = await self.renderer.render_elements(model.elements)

        # Render systems section
        systems_section = await self.renderer.render_systems(model.systems)

        # Combine sections
        ascii_content = f"{building_section}\n\n{elements_section}\n\n{systems_section}"

        return ascii_content

    async def validate_ascii_bim(self, content: str) -> ValidationResult:
        """Validate ASCII-BIM syntax and structure"""

        try:
            # Parse content to check syntax
            model = await self.parse_ascii_bim(content)

            # Validate structure
            structure_errors = await self.validator.validate_structure(model)

            # Validate data types
            type_errors = await self.validator.validate_data_types(model)

            # Validate relationships
            relationship_errors = await self.validator.validate_relationships(model)

            # Combine all errors
            all_errors = structure_errors + type_errors + relationship_errors

            return ValidationResult(
                is_valid=len(all_errors) == 0,
                errors=all_errors,
                warnings=await self.validator.get_warnings(model)
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Parsing error: {str(e)}"],
                warnings=[]
            )

    async def convert_to_svgx(self, ascii_content: str) -> SVGXModel:
        """Convert ASCII-BIM to SVGX format"""

        # Parse ASCII-BIM
        ascii_model = await self.parse_ascii_bim(ascii_content)

        # Convert building
        svgx_building = await self.converter.convert_building(ascii_model.building)

        # Convert elements
        svgx_elements = await self.converter.convert_elements(ascii_model.elements)

        # Convert systems
        svgx_systems = await self.converter.convert_systems(ascii_model.systems)

        # Create SVGX model
        svgx_model = SVGXModel(
            building=svgx_building,
            elements=svgx_elements,
            systems=svgx_systems,
            metadata=ascii_model.metadata
        )

        return svgx_model

    async def convert_from_svgx(self, svgx_model: SVGXModel) -> str:
        """Convert SVGX to ASCII-BIM format"""

        # Convert building
        ascii_building = await self.converter.convert_svgx_building(svgx_model.building)

        # Convert elements
        ascii_elements = await self.converter.convert_svgx_elements(svgx_model.elements)

        # Convert systems
        ascii_systems = await self.converter.convert_svgx_systems(svgx_model.systems)

        # Create ASCII-BIM content
        ascii_content = f"{ascii_building}\n\n{ascii_elements}\n\n{ascii_systems}"

        return ascii_content
```

### **1.2 ASCII-BIM Parser**

```python
# arxos/svgx_engine/services/ascii_bim_parser.py
class ASCIIBIMParser:
    """Parse ASCII-BIM format into structured data"""

    def __init__(self):
        self.building_parser = BuildingParser()
        self.element_parser = ElementParser()
        self.system_parser = SystemParser()
        self.property_parser = PropertyParser()

    def parse_building_block(self, lines: List[str]) -> Building:
        """Parse BUILDING { ... } block"""

        building_lines = self.extract_block(lines, "BUILDING")
        if not building_lines:
            raise ValueError("No BUILDING block found")

        building_data = {}

        for line in building_lines:
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                building_data[key] = value

        return Building(
            id=building_data.get('id', ''),
            name=building_data.get('name', ''),
            type=building_data.get('type', ''),
            address=building_data.get('address', ''),
            coordinates=building_data.get('coordinates', ''),
            properties=building_data
        )

    def parse_elements_block(self, lines: List[str]) -> List[Element]:
        """Parse ELEMENTS { ... } block"""

        elements_lines = self.extract_block(lines, "ELEMENTS")
        if not elements_lines:
            return []

        elements = []
        current_element = {}

        for line in elements_lines:
            line = line.strip()

            if line.startswith('ELEMENT'):
                # Save previous element
                if current_element:
                    elements.append(self.create_element(current_element))

                # Start new element
                current_element = {'type': line.split()[1]}

            elif '=' in line and current_element:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                current_element[key] = value

        # Add last element
        if current_element:
            elements.append(self.create_element(current_element))

        return elements

    def parse_systems_block(self, lines: List[str]) -> List[System]:
        """Parse SYSTEMS { ... } block"""

        systems_lines = self.extract_block(lines, "SYSTEMS")
        if not systems_lines:
            return []

        systems = []
        current_system = {}

        for line in systems_lines:
            line = line.strip()

            if line.startswith('SYSTEM'):
                # Save previous system
                if current_system:
                    systems.append(self.create_system(current_system))

                # Start new system
                current_system = {'type': line.split()[1]}

            elif '=' in line and current_system:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                current_system[key] = value

        # Add last system
        if current_system:
            systems.append(self.create_system(current_system))

        return systems

    def parse_properties(self, lines: List[str]) -> Dict[str, Any]:
        """Parse element properties"""

        properties = {}

        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')

                # Try to parse as number
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass  # Keep as string

                properties[key] = value

        return properties

    def extract_block(self, lines: List[str], block_name: str) -> List[str]:
        """Extract lines within a specific block"""

        block_lines = []
        in_block = False
        brace_count = 0

        for line in lines:
            if block_name in line and '{' in line:
                in_block = True
                brace_count = 1
                continue

            if in_block:
                if '{' in line:
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')

                if brace_count == 0:
                    break

                block_lines.append(line)

        return block_lines

    def create_element(self, data: Dict[str, Any]) -> Element:
        """Create Element object from parsed data"""

        return Element(
            id=data.get('id', ''),
            type=data.get('type', ''),
            name=data.get('name', ''),
            location=data.get('location', ''),
            properties=data
        )

    def create_system(self, data: Dict[str, Any]) -> System:
        """Create System object from parsed data"""

        return System(
            id=data.get('id', ''),
            type=data.get('type', ''),
            name=data.get('name', ''),
            elements=data.get('elements', []),
            properties=data
        )
```

### **1.3 ASCII-BIM Renderer**

```python
# arxos/svgx_engine/services/ascii_bim_renderer.py
class ASCIIBIMRenderer:
    """Render structured data to ASCII-BIM format"""

    def __init__(self):
        self.building_renderer = BuildingRenderer()
        self.element_renderer = ElementRenderer()
        self.system_renderer = SystemRenderer()

    def render_building(self, building: Building) -> str:
        """Render building information"""

        lines = [
            "BUILDING {",
            f"    id = \"{building.id}\"",
            f"    name = \"{building.name}\"",
            f"    type = \"{building.type}\"",
            f"    address = \"{building.address}\"",
            f"    coordinates = \"{building.coordinates}\""
        ]

        # Add custom properties
        for key, value in building.properties.items():
            if key not in ['id', 'name', 'type', 'address', 'coordinates']:
                if isinstance(value, str):
                    lines.append(f"    {key} = \"{value}\"")
                else:
                    lines.append(f"    {key} = {value}")

        lines.append("}")
        return "\n".join(lines)

    def render_elements(self, elements: List[Element]) -> str:
        """Render elements section"""

        if not elements:
            return "ELEMENTS {\n}"

        lines = ["ELEMENTS {"]

        for element in elements:
            lines.extend(self.render_element(element))
            lines.append("")  # Empty line between elements

        lines.append("}")
        return "\n".join(lines)

    def render_element(self, element: Element) -> List[str]:
        """Render individual element"""

        lines = [
            f"    ELEMENT {element.type} {{",
            f"        id = \"{element.id}\"",
            f"        name = \"{element.name}\"",
            f"        location = \"{element.location}\""
        ]

        # Add custom properties
        for key, value in element.properties.items():
            if key not in ['id', 'name', 'location']:
                if isinstance(value, str):
                    lines.append(f"        {key} = \"{value}\"")
                else:
                    lines.append(f"        {key} = {value}")

        lines.append("    }")
        return lines

    def render_systems(self, systems: List[System]) -> str:
        """Render systems section"""

        if not systems:
            return "SYSTEMS {\n}"

        lines = ["SYSTEMS {"]

        for system in systems:
            lines.extend(self.render_system(system))
            lines.append("")  # Empty line between systems

        lines.append("}")
        return "\n".join(lines)

    def render_system(self, system: System) -> List[str]:
        """Render individual system"""

        lines = [
            f"    SYSTEM {system.type} {{",
            f"        id = \"{system.id}\"",
            f"        name = \"{system.name}\""
        ]

        # Add elements if present
        if system.elements:
            elements_str = ", ".join(system.elements)
            lines.append(f"        elements = \"{elements_str}\"")

        # Add custom properties
        for key, value in system.properties.items():
            if key not in ['id', 'name', 'elements']:
                if isinstance(value, str):
                    lines.append(f"        {key} = \"{value}\"")
                else:
                    lines.append(f"        {key} = {value}")

        lines.append("    }")
        return lines
```

### **1.4 ASCII-BIM Validator**

```python
# arxos/svgx_engine/services/ascii_bim_validator.py
class ASCIIBIMValidator:
    """Validate ASCII-BIM syntax and structure"""

    def __init__(self):
        self.syntax_validator = SyntaxValidator()
        self.structure_validator = StructureValidator()
        self.data_type_validator = DataTypeValidator()
        self.relationship_validator = RelationshipValidator()

    async def validate_structure(self, model: ASCIIBIMModel) -> List[str]:
        """Validate model structure"""

        errors = []

        # Validate building
        if not model.building:
            errors.append("Missing building information")
        elif not model.building.id:
            errors.append("Building must have an ID")

        # Validate elements
        if not model.elements:
            errors.append("No elements defined")

        for element in model.elements:
            if not element.id:
                errors.append(f"Element {element.type} must have an ID")
            if not element.type:
                errors.append(f"Element {element.id} must have a type")

        # Validate systems
        for system in model.systems:
            if not system.id:
                errors.append(f"System {system.type} must have an ID")
            if not system.type:
                errors.append(f"System {system.id} must have a type")

        return errors

    async def validate_data_types(self, model: ASCIIBIMModel) -> List[str]:
        """Validate data types"""

        errors = []

        # Validate building data types
        if model.building:
            errors.extend(await self.validate_building_data_types(model.building))

        # Validate element data types
        for element in model.elements:
            errors.extend(await self.validate_element_data_types(element))

        # Validate system data types
        for system in model.systems:
            errors.extend(await self.validate_system_data_types(system))

        return errors

    async def validate_relationships(self, model: ASCIIBIMModel) -> List[str]:
        """Validate relationships between components"""

        errors = []

        # Check for duplicate IDs
        element_ids = [e.id for e in model.elements]
        if len(element_ids) != len(set(element_ids)):
            errors.append("Duplicate element IDs found")

        system_ids = [s.id for s in model.systems]
        if len(system_ids) != len(set(system_ids)):
            errors.append("Duplicate system IDs found")

        # Check system-element relationships
        for system in model.systems:
            for element_id in system.elements:
                if element_id not in element_ids:
                    errors.append(f"System {system.id} references non-existent element {element_id}")

        return errors

    async def get_warnings(self, model: ASCIIBIMModel) -> List[str]:
        """Get validation warnings"""

        warnings = []

        # Check for missing optional fields
        for element in model.elements:
            if not element.name:
                warnings.append(f"Element {element.id} has no name")
            if not element.location:
                warnings.append(f"Element {element.id} has no location")

        for system in model.systems:
            if not system.name:
                warnings.append(f"System {system.id} has no name")
            if not system.elements:
                warnings.append(f"System {system.id} has no elements")

        return warnings
```

### **1.5 ASCII-BIM Converter**

```python
# arxos/svgx_engine/services/ascii_bim_converter.py
class ASCIIBIMConverter:
    """Convert between ASCII-BIM and SVGX formats"""

    def __init__(self):
        self.building_converter = BuildingConverter()
        self.element_converter = ElementConverter()
        self.system_converter = SystemConverter()

    async def convert_building(self, building: Building) -> SVGXBuilding:
        """Convert ASCII-BIM building to SVGX format"""

        return SVGXBuilding(
            id=building.id,
            name=building.name,
            type=building.type,
            address=building.address,
            coordinates=building.coordinates,
            properties=building.properties
        )

    async def convert_elements(self, elements: List[Element]) -> List[SVGXElement]:
        """Convert ASCII-BIM elements to SVGX format"""

        svgx_elements = []

        for element in elements:
            svgx_element = SVGXElement(
                id=element.id,
                type=element.type,
                name=element.name,
                location=element.location,
                properties=element.properties
            )
            svgx_elements.append(svgx_element)

        return svgx_elements

    async def convert_systems(self, systems: List[System]) -> List[SVGXSystem]:
        """Convert ASCII-BIM systems to SVGX format"""

        svgx_systems = []

        for system in systems:
            svgx_system = SVGXSystem(
                id=system.id,
                type=system.type,
                name=system.name,
                elements=system.elements,
                properties=system.properties
            )
            svgx_systems.append(svgx_system)

        return svgx_systems

    async def convert_svgx_building(self, building: SVGXBuilding) -> Building:
        """Convert SVGX building to ASCII-BIM format"""

        return Building(
            id=building.id,
            name=building.name,
            type=building.type,
            address=building.address,
            coordinates=building.coordinates,
            properties=building.properties
        )

    async def convert_svgx_elements(self, elements: List[SVGXElement]) -> List[Element]:
        """Convert SVGX elements to ASCII-BIM format"""

        ascii_elements = []

        for element in elements:
            ascii_element = Element(
                id=element.id,
                type=element.type,
                name=element.name,
                location=element.location,
                properties=element.properties
            )
            ascii_elements.append(ascii_element)

        return ascii_elements

    async def convert_svgx_systems(self, systems: List[SVGXSystem]) -> List[System]:
        """Convert SVGX systems to ASCII-BIM format"""

        ascii_systems = []

        for system in systems:
            ascii_system = System(
                id=system.id,
                type=system.type,
                name=system.name,
                elements=system.elements,
                properties=system.properties
            )
            ascii_systems.append(ascii_system)

        return ascii_systems
```

---

## 🚀 **Implementation Roadmap**

### **Phase 1: Core Parser (Week 1-2)**
- [ ] ASCII-BIM parser implementation
- [ ] Basic validation system
- [ ] Unit tests for parser
- [ ] Integration with existing export system

### **Phase 2: Renderer & Converter (Week 3-4)**
- [ ] ASCII-BIM renderer implementation
- [ ] SVGX converter implementation
- [ ] Bidirectional conversion testing
- [ ] Performance optimization

### **Phase 3: Advanced Features (Week 5-6)**
- [ ] Advanced validation rules
- [ ] Diff/merge functionality
- [ ] Visualization tools
- [ ] CLI integration

### **Phase 4: Production Ready (Week 7-8)**
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Performance optimization
- [ ] Production deployment

---

## 📊 **Success Metrics**

### **Performance Targets**
- **Parsing Speed**: < 100ms for typical files
- **Rendering Speed**: < 50ms for typical files
- **Conversion Speed**: < 200ms for SVGX conversion
- **Memory Usage**: < 50MB for large files

### **Quality Targets**
- **Validation Accuracy**: > 95% error detection
- **Conversion Accuracy**: > 99% data preservation
- **Test Coverage**: > 90% code coverage
- **Documentation Coverage**: 100% API documentation

---

## 🔧 **API Integration**

### **FastAPI Endpoints**

```python
# arxos/svgx_engine/api/ascii_bim_api.py
from fastapi import FastAPI, UploadFile, File
from svgx_engine.services.ascii_bim_engine import ASCIIBIMEngine

app = FastAPI()
engine = ASCIIBIMEngine()

@app.post("/ascii-bim/parse")
async def parse_ascii_bim(file: UploadFile = File(...)):
    """Parse ASCII-BIM file"""
    content = await file.read()
    model = await engine.parse_ascii_bim(content.decode())
    return model

@app.post("/ascii-bim/render")
async def render_ascii_bim(model: ASCIIBIMModel):
    """Render model to ASCII-BIM format"""
    content = await engine.render_ascii_bim(model)
    return {"content": content}

@app.post("/ascii-bim/validate")
async def validate_ascii_bim(file: UploadFile = File(...)):
    """Validate ASCII-BIM file"""
    content = await file.read()
    result = await engine.validate_ascii_bim(content.decode())
    return result

@app.post("/ascii-bim/convert-to-svgx")
async def convert_to_svgx(file: UploadFile = File(...)):
    """Convert ASCII-BIM to SVGX"""
    content = await file.read()
    svgx_model = await engine.convert_to_svgx(content.decode())
    return svgx_model

@app.post("/ascii-bim/convert-from-svgx")
async def convert_from_svgx(svgx_model: SVGXModel):
    """Convert SVGX to ASCII-BIM"""
    content = await engine.convert_from_svgx(svgx_model)
    return {"content": content}
```

The ASCII-BIM System provides comprehensive format processing capabilities with parsing, rendering, validation, and conversion features for seamless integration with the Arxos platform.
