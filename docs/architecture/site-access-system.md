# Site Access System Architecture

## 🎯 **System Overview**

**Universal three-tier site access system** enabling users to create physical references to Arxos SVGX views for **any building system**:
1. **Shortened URLs** - Primary method for instant site access
2. **NFC Framework** - Optional enhancement for tap-to-access
3. **Hub Search** - Default fallback for building discovery

### **Universal Building System Support**
This system works for **all building systems and equipment**:
- **Electrical**: Panels, circuits, outlets, lighting
- **HVAC**: Air handlers, chillers, thermostats, ductwork
- **Plumbing**: Pumps, valves, fixtures, piping
- **Fire Protection**: Sprinklers, alarms, extinguishers
- **Security**: Cameras, access control, sensors
- **AV/IT**: Network equipment, speakers, displays
- **Mechanical**: Elevators, escalators, conveyors
- **Structural**: Beams, columns, foundations
- **Roofing**: Drains, vents, equipment
- **Landscaping**: Irrigation, lighting, hardscape

---

## 🏗️ **High-Level Architecture**

### **Core Components**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   URL Service   │    │   NFC Service   │    │   Hub Service   │
│                 │    │                 │    │                 │
│ • URL Shortener │    │ • NFC Generator │    │ • Building      │
│ • View Mapping  │    │ • Tag Manager   │    │   Directory     │
│ • Analytics     │    │ • Tap Handler   │    │ • Search Engine │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Core Engine   │
                    │                 │
                    │ • View Manager  │
                    │ • Access Control│
                    │ • Analytics     │
                    └─────────────────┘
```

---

## 🔗 **Shortened URL System**

### **URL Service Architecture**
```python
class SiteURLService:
    """Manage shortened URLs for site access across all building systems"""

    def __init__(self):
        self.url_generator = URLGenerator()
        self.view_mapper = ViewMapper()
        self.analytics = URLAnalytics()
        self.access_control = AccessControl()

    def create_site_url(self, user_id: str, view_config: ViewConfig,
                       custom_slug: str = None, password: str = None) -> SiteURL:
        """Create shortened URL for specific SVGX view of any building system"""

        # Generate unique slug
        slug = custom_slug or self.url_generator.generate_slug()

        # Create view mapping
        view_mapping = self.view_mapper.create_mapping(
            user_id=user_id,
            view_config=view_config,
            slug=slug
        )

        # Create access control
        access_config = AccessConfig(
            password_protected=bool(password),
            password_hash=self.hash_password(password) if password else None,
            expires_at=self.calculate_expiry(view_config.access_type),
            max_uses=view_config.max_uses
        )

        # Create site URL
        site_url = SiteURL(
            slug=slug,
            full_url=f"https://arxos.com/p/{slug}",
            view_mapping=view_mapping,
            access_config=access_config,
            created_at=datetime.now(),
            created_by=user_id
        )

        # Store in database
        self.store_site_url(site_url)

        return site_url

    def resolve_site_url(self, slug: str, password: str = None) -> ViewConfig:
        """Resolve shortened URL to view configuration for any building system"""

        # Get site URL
        site_url = self.get_site_url(slug)

        if not site_url:
            raise URLNotFoundError(f"Site URL not found: {slug}")

        # Check access control
        access_granted = self.access_control.check_access(
            site_url.access_config,
            password=password
        )

        if not access_granted:
            raise AccessDeniedError("Access denied to this site URL")

        # Log access
        self.analytics.log_access(site_url, password_provided=bool(password))

        # Return view configuration
        return site_url.view_mapping.view_config

    def update_site_url(self, slug: str, updates: dict) -> SiteURL:
        """Update site URL configuration"""

        site_url = self.get_site_url(slug)

        # Apply updates
        for field, value in updates.items():
            if hasattr(site_url, field):
                setattr(site_url, field, value)

        # Update in database
        self.update_site_url(site_url)

        return site_url

    def get_analytics(self, slug: str) -> URLAnalytics:
        """Get analytics for site URL"""

        return self.analytics.get_analytics(slug)
```

### **View Mapping System**
```python
class ViewMapper:
    """Map shortened URLs to specific SVGX views for all building systems"""

    def create_mapping(self, user_id: str, view_config: ViewConfig, slug: str) -> ViewMapping:
        """Create mapping between slug and SVGX view for any building system"""

        # Capture current view state
        view_state = self.capture_view_state(view_config)

        # Create mapping
        mapping = ViewMapping(
            slug=slug,
            user_id=user_id,
            view_config=view_config,
            view_state=view_state,
            created_at=datetime.now()
        )

        return mapping

    def capture_view_state(self, view_config: ViewConfig) -> ViewState:
        """Capture current state of SVGX view for any building system"""

        return ViewState(
            building_id=view_config.building_id,
            floor_id=view_config.floor_id,
            system_type=view_config.system_type,  # electrical, hvac, plumbing, etc.
            equipment_id=view_config.equipment_id,  # specific equipment if applicable
            zoom_level=view_config.zoom_level,
            center_coordinates=view_config.center_coordinates,
            visible_layers=view_config.visible_layers,
            selected_objects=view_config.selected_objects,
            filters=view_config.filters,
            system_specific_config=view_config.system_specific_config  # HVAC filters, electrical phases, etc.
        )

    def restore_view_state(self, view_state: ViewState) -> ViewConfig:
        """Restore view configuration from captured state for any building system"""

        return ViewConfig(
            building_id=view_state.building_id,
            floor_id=view_state.floor_id,
            system_type=view_state.system_type,
            equipment_id=view_state.equipment_id,
            zoom_level=view_state.zoom_level,
            center_coordinates=view_state.center_coordinates,
            visible_layers=view_state.visible_layers,
            selected_objects=view_state.selected_objects,
            filters=view_state.filters,
            system_specific_config=view_state.system_specific_config
        )
```

### **System-Specific Configuration**
```python
class SystemSpecificConfig:
    """Configuration specific to different building systems"""

    @dataclass
    class ElectricalConfig:
        phase: str = None  # A, B, C, or all
        voltage: str = None  # 120V, 240V, 480V, etc.
        circuit_type: str = None  # lighting, power, emergency
        panel_id: str = None

    @dataclass
    class HVACConfig:
        zone: str = None
        equipment_type: str = None  # AHU, chiller, thermostat
        temperature_setpoint: float = None
        airflow: str = None

    @dataclass
    class PlumbingConfig:
        pipe_size: str = None
        material: str = None  # copper, pvc, steel
        flow_rate: float = None
        pressure: float = None

    @dataclass
    class FireProtectionConfig:
        sprinkler_type: str = None
        coverage_area: str = None
        flow_rate: float = None
        pressure: float = None

    @dataclass
    class SecurityConfig:
        camera_type: str = None
        recording_quality: str = None
        motion_detection: bool = None
        access_level: str = None

    @dataclass
    class AVConfig:
        speaker_type: str = None
        amplifier_power: str = None
        signal_type: str = None  # audio, video, control
        zone: str = None
```

---

## 📱 **NFC Framework**

### **NFC Service Architecture**
```python
class NFCService:
    """Manage NFC tags for site access across all building systems"""

    def __init__(self):
        self.nfc_generator = NFCGenerator()
        self.tag_manager = TagManager()
        self.tap_handler = TapHandler()
        self.url_service = SiteURLService()

    def create_nfc_tag(self, user_id: str, view_config: ViewConfig,
                       tag_type: str = 'standard', equipment_info: dict = None) -> NFCTag:
        """Create NFC tag for site access to any building system"""

        # Create site URL first
        site_url = self.url_service.create_site_url(user_id, view_config)

        # Generate NFC data with system-specific information
        nfc_data = self.nfc_generator.generate_nfc_data(
            site_url=site_url,
            tag_type=tag_type,
            equipment_info=equipment_info
        )

        # Create NFC tag
        nfc_tag = NFCTag(
            tag_id=self.generate_tag_id(),
            nfc_data=nfc_data,
            site_url=site_url,
            tag_type=tag_type,
            equipment_info=equipment_info,
            created_at=datetime.now(),
            created_by=user_id
        )

        # Store in database
        self.tag_manager.store_tag(nfc_tag)

        return nfc_tag

    def handle_nfc_tap(self, nfc_data: bytes) -> ViewConfig:
        """Handle NFC tap and return view configuration for any building system"""

        # Decode NFC data
        decoded_data = self.nfc_generator.decode_nfc_data(nfc_data)

        # Extract site URL slug
        slug = decoded_data.get('slug')

        if not slug:
            raise NFCDataError("Invalid NFC data format")

        # Resolve site URL
        view_config = self.url_service.resolve_site_url(slug)

        # Log tap with system information
        self.tap_handler.log_tap(slug, nfc_data, decoded_data.get('system_type'))

        return view_config

    def generate_nfc_data(self, site_url: SiteURL, tag_type: str,
                          equipment_info: dict = None) -> bytes:
        """Generate NFC data for tag with system-specific information"""

        # Create NFC payload with system context
        payload = {
            'type': 'arxos_site_access',
            'slug': site_url.slug,
            'version': '1.0',
            'created_at': site_url.created_at.isoformat(),
            'system_type': site_url.view_mapping.view_config.system_type,
            'equipment_info': equipment_info or {}
        }

        # Encode based on tag type
        if tag_type == 'standard':
            return self.encode_standard_nfc(payload)
        elif tag_type == 'encrypted':
            return self.encode_encrypted_nfc(payload)
        else:
            raise ValueError(f"Unknown tag type: {tag_type}")
```

---

## 🔍 **Hub Search System**

### **Hub Service Architecture**
```python
class HubService:
    """Manage building discovery and search across all building systems"""

    def __init__(self):
        self.search_engine = BuildingSearchEngine()
        self.directory = BuildingDirectory()
        self.geolocation = GeolocationService()
        self.system_filter = SystemFilter()

    def search_buildings(self, query: str, filters: dict = None) -> SearchResults:
        """Search for buildings and systems in the system"""

        # Parse search query
        parsed_query = self.search_engine.parse_query(query)

        # Apply filters including system-specific filters
        search_filters = self.build_search_filters(parsed_query, filters)

        # Execute search
        results = self.search_engine.search(parsed_query, search_filters)

        return SearchResults(
            query=query,
            results=results,
            total_count=len(results),
            search_time=results.search_time
        )

    def search_by_system(self, system_type: str, location: str = None) -> SystemSearchResults:
        """Search for specific building systems"""

        # Build system-specific search criteria
        criteria = SearchCriteria(
            system_type=system_type,
            location=location,
            include_equipment=True
        )

        # Execute system search
        results = self.search_engine.search_by_system(criteria)

        return SystemSearchResults(
            system_type=system_type,
            results=results,
            total_count=len(results)
        )

    def get_nearby_buildings(self, latitude: float, longitude: float,
                            radius_km: float = 10.0, system_type: str = None) -> NearbyBuildings:
        """Get buildings near specified location, optionally filtered by system"""

        # Find buildings within radius
        nearby = self.geolocation.find_nearby_buildings(
            latitude, longitude, radius_km, system_type
        )

        return NearbyBuildings(
            center_lat=latitude,
            center_lng=longitude,
            radius_km=radius_km,
            buildings=nearby,
            system_type=system_type
        )

    def get_building_directory(self, filters: dict = None) -> BuildingDirectory:
        """Get public building directory with system information"""

        # Get public buildings with system details
        public_buildings = self.directory.get_public_buildings(filters)

        return BuildingDirectory(
            buildings=public_buildings,
            total_count=len(public_buildings),
            filters_applied=filters
        )
```

### **System-Specific Search**
```python
class SystemFilter:
    """Filter and search by building system types"""

    def __init__(self):
        self.system_definitions = self.load_system_definitions()

    def load_system_definitions(self) -> dict:
        """Load definitions for all building systems"""

        return {
            'electrical': {
                'name': 'Electrical Systems',
                'equipment': ['panels', 'circuits', 'outlets', 'lighting', 'transformers'],
                'keywords': ['voltage', 'amperage', 'phase', 'breaker', 'conduit']
            },
            'hvac': {
                'name': 'HVAC Systems',
                'equipment': ['air_handlers', 'chillers', 'thermostats', 'ductwork', 'vents'],
                'keywords': ['temperature', 'airflow', 'cooling', 'heating', 'ventilation']
            },
            'plumbing': {
                'name': 'Plumbing Systems',
                'equipment': ['pumps', 'valves', 'fixtures', 'piping', 'drains'],
                'keywords': ['flow_rate', 'pressure', 'pipe_size', 'material']
            },
            'fire_protection': {
                'name': 'Fire Protection',
                'equipment': ['sprinklers', 'alarms', 'extinguishers', 'detectors'],
                'keywords': ['coverage', 'flow_rate', 'pressure', 'detection']
            },
            'security': {
                'name': 'Security Systems',
                'equipment': ['cameras', 'access_control', 'sensors', 'alarms'],
                'keywords': ['surveillance', 'access', 'motion', 'recording']
            },
            'av': {
                'name': 'Audio/Visual Systems',
                'equipment': ['speakers', 'displays', 'amplifiers', 'projectors'],
                'keywords': ['audio', 'video', 'sound', 'display', 'control']
            },
            'mechanical': {
                'name': 'Mechanical Systems',
                'equipment': ['elevators', 'escalators', 'conveyors', 'fans'],
                'keywords': ['motion', 'transport', 'mechanical', 'drive']
            },
            'structural': {
                'name': 'Structural Systems',
                'equipment': ['beams', 'columns', 'foundations', 'walls'],
                'keywords': ['load', 'support', 'foundation', 'structural']
            }
        }

    def filter_by_system(self, buildings: List[Building], system_type: str) -> List[Building]:
        """Filter buildings by specific system type"""

        filtered_buildings = []

        for building in buildings:
            if self.has_system(building, system_type):
                filtered_buildings.append(building)

        return filtered_buildings

    def has_system(self, building: Building, system_type: str) -> bool:
        """Check if building has specific system"""

        # Check building systems
        if system_type in building.systems:
            return True

        # Check equipment inventory
        for equipment in building.equipment:
            if equipment.system_type == system_type:
                return True

        return False
```

---

## 🗄️ **Database Schema**

### **Site URLs Table (Updated)**
```sql
CREATE TABLE site_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    view_config JSONB NOT NULL,
    access_config JSONB DEFAULT '{}',
    system_type VARCHAR(50),  -- electrical, hvac, plumbing, etc.
    equipment_id UUID,        -- specific equipment if applicable
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- Indexes
    INDEX idx_site_urls_slug (slug),
    INDEX idx_site_urls_user_id (user_id),
    INDEX idx_site_urls_system_type (system_type),
    INDEX idx_site_urls_equipment_id (equipment_id),
    INDEX idx_site_urls_created_at (created_at)
);
```

### **NFC Tags Table (Updated)**
```sql
CREATE TABLE nfc_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_id VARCHAR(100) UNIQUE NOT NULL,
    site_url_id UUID REFERENCES site_urls(id),
    nfc_data BYTEA NOT NULL,
    tag_type VARCHAR(20) DEFAULT 'standard',
    system_type VARCHAR(50),  -- electrical, hvac, plumbing, etc.
    equipment_info JSONB,     -- system-specific equipment information
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    -- Indexes
    INDEX idx_nfc_tags_tag_id (tag_id),
    INDEX idx_nfc_tags_site_url_id (site_url_id),
    INDEX idx_nfc_tags_system_type (system_type),
    INDEX idx_nfc_tags_status (status)
);
```

### **Building Systems Table**
```sql
CREATE TABLE building_systems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID REFERENCES buildings(id),
    system_type VARCHAR(50) NOT NULL,  -- electrical, hvac, plumbing, etc.
    system_name VARCHAR(255),
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_building_systems_building_id (building_id),
    INDEX idx_building_systems_system_type (system_type),
    INDEX idx_building_systems_status (status)
);
```

### **Equipment Table**
```sql
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID REFERENCES buildings(id),
    system_type VARCHAR(50) NOT NULL,  -- electrical, hvac, plumbing, etc.
    equipment_type VARCHAR(100),       -- panel, air_handler, pump, etc.
    name VARCHAR(255),
    location_description TEXT,
    specifications JSONB,              -- system-specific specifications
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_equipment_building_id (building_id),
    INDEX idx_equipment_system_type (system_type),
    INDEX idx_equipment_equipment_type (equipment_type),
    INDEX idx_equipment_status (status)
);
```

---

## 🔌 **API Endpoints**

### **Site URL Endpoints (Updated)**
```python
# Create site URL for any building system
POST /api/v1/site-urls
{
    "view_config": {
        "building_id": "uuid",
        "system_type": "hvac",  # electrical, hvac, plumbing, fire_protection, etc.
        "equipment_id": "uuid",  # optional - specific equipment
        "zoom_level": 1.5,
        "center_coordinates": [x, y],
        "system_specific_config": {
            "zone": "zone-1",
            "equipment_type": "air_handler"
        }
    },
    "custom_slug": "hvac-zone-1",  # optional
    "password": "secret123",        # optional
    "expires_at": "2025-12-31",     # optional
    "max_uses": 100                 # optional
}

# Search site URLs by system type
GET /api/v1/site-urls?system_type=hvac&building_id=uuid

# Get site URLs for specific equipment
GET /api/v1/site-urls?equipment_id=uuid
```

### **System-Specific Endpoints**
```python
# Get all systems for a building
GET /api/v1/buildings/{building_id}/systems

# Get equipment for specific system
GET /api/v1/buildings/{building_id}/systems/{system_type}/equipment

# Create equipment record
POST /api/v1/equipment
{
    "building_id": "uuid",
    "system_type": "electrical",
    "equipment_type": "panel",
    "name": "Main Electrical Panel",
    "location_description": "Basement electrical room",
    "specifications": {
        "voltage": "480V",
        "amperage": "400A",
        "phases": 3
    }
}
```

### **Hub Search Endpoints (Updated)**
```python
# Search buildings by system type
GET /api/v1/hub/search?q=electrical+panel&system_type=electrical

# Get buildings with specific system
GET /api/v1/hub/systems/{system_type}/buildings

# Get nearby buildings with specific system
GET /api/v1/hub/nearby?lat=40.7128&lng=-74.0060&radius=10&system_type=hvac

# Get equipment directory for system type
GET /api/v1/hub/systems/{system_type}/equipment
```

---

## 🎨 **Frontend Components**

### **System-Specific URL Creation**
```typescript
interface SystemSpecificURLCreationProps {
    currentView: ViewConfig;
    systemType: string;
    equipment?: Equipment;
    onURLCreated: (siteURL: SiteURL) => void;
}

const SystemSpecificURLCreation: React.FC<SystemSpecificURLCreationProps> = ({
    currentView,
    systemType,
    equipment,
    onURLCreated
}) => {
    const [customSlug, setCustomSlug] = useState('');
    const [password, setPassword] = useState('');
    const [expiresAt, setExpiresAt] = useState('');
    const [maxUses, setMaxUses] = useState(0);

    const getSystemSpecificFields = () => {
        switch (systemType) {
            case 'electrical':
                return (
                    <div className="electrical-fields">
                        <label>Panel ID</label>
                        <input type="text" placeholder="Panel A-12" />
                        <label>Phase</label>
                        <select>
                            <option value="all">All Phases</option>
                            <option value="A">Phase A</option>
                            <option value="B">Phase B</option>
                            <option value="C">Phase C</option>
                        </select>
                    </div>
                );
            case 'hvac':
                return (
                    <div className="hvac-fields">
                        <label>Zone</label>
                        <input type="text" placeholder="Zone 1" />
                        <label>Equipment Type</label>
                        <select>
                            <option value="air_handler">Air Handler</option>
                            <option value="thermostat">Thermostat</option>
                            <option value="chiller">Chiller</option>
                        </select>
                    </div>
                );
            case 'plumbing':
                return (
                    <div className="plumbing-fields">
                        <label>Pipe Size</label>
                        <input type="text" placeholder="2 inch" />
                        <label>Material</label>
                        <select>
                            <option value="copper">Copper</option>
                            <option value="pvc">PVC</option>
                            <option value="steel">Steel</option>
                        </select>
                    </div>
                );
            default:
                return null;
        }
    };

    const createSiteURL = async () => {
        const response = await api.post('/site-urls', {
            view_config: {
                ...currentView,
                system_type: systemType,
                equipment_id: equipment?.id,
                system_specific_config: getSystemSpecificConfig()
            },
            custom_slug: customSlug || undefined,
            password: password || undefined,
            expires_at: expiresAt || undefined,
            max_uses: maxUses || undefined
        });

        onURLCreated(response.data);
    };

    return (
        <div className="system-specific-url-creation">
            <h3>Create {getSystemName(systemType)} Access Link</h3>

            {equipment && (
                <div className="equipment-info">
                    <h4>Equipment: {equipment.name}</h4>
                    <p>{equipment.location_description}</p>
                </div>
            )}

            {getSystemSpecificFields()}

            <div className="form-group">
                <label>Custom URL (optional)</label>
                <input
                    type="text"
                    value={customSlug}
                    onChange={(e) => setCustomSlug(e.target.value)}
                    placeholder={`${systemType}-${equipment?.name || 'location'}`}
                />
            </div>

            <div className="form-group">
                <label>Password Protection (optional)</label>
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                />
            </div>

            <button onClick={createSiteURL}>
                Create {getSystemName(systemType)} Access Link
            </button>
        </div>
    );
};
```

### **System-Specific Hub Search**
```typescript
interface SystemSpecificHubSearchProps {
    systemType?: string;
    onBuildingSelected: (building: Building) => void;
    onEquipmentSelected: (equipment: Equipment) => void;
}

const SystemSpecificHubSearch: React.FC<SystemSpecificHubSearchProps> = ({
    systemType,
    onBuildingSelected,
    onEquipmentSelected
}) => {
    const [query, setQuery] = useState('');
    const [selectedSystem, setSelectedSystem] = useState(systemType || '');
    const [results, setResults] = useState<SearchResults>([]);
    const [loading, setLoading] = useState(false);

    const systemTypes = [
        { value: 'electrical', label: 'Electrical Systems' },
        { value: 'hvac', label: 'HVAC Systems' },
        { value: 'plumbing', label: 'Plumbing Systems' },
        { value: 'fire_protection', label: 'Fire Protection' },
        { value: 'security', label: 'Security Systems' },
        { value: 'av', label: 'Audio/Visual Systems' },
        { value: 'mechanical', label: 'Mechanical Systems' },
        { value: 'structural', label: 'Structural Systems' }
    ];

    const searchBuildings = async () => {
        setLoading(true);

        try {
            const params: any = { q: query };
            if (selectedSystem) {
                params.system_type = selectedSystem;
            }

            const response = await api.get('/hub/search', { params });
            setResults(response.data);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="system-specific-hub-search">
            <h2>Find Buildings & Systems</h2>

            <div className="search-form">
                <div className="system-filter">
                    <label>System Type</label>
                    <select
                        value={selectedSystem}
                        onChange={(e) => setSelectedSystem(e.target.value)}
                    >
                        <option value="">All Systems</option>
                        {systemTypes.map(system => (
                            <option key={system.value} value={system.value}>
                                {system.label}
                            </option>
                        ))}
                    </select>
                </div>

                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search by address, building name, or equipment..."
                    onKeyPress={(e) => e.key === 'Enter' && searchBuildings()}
                />

                <button onClick={searchBuildings} disabled={loading}>
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </div>

            {results.length > 0 && (
                <div className="search-results">
                    <h3>Found {results.length} results</h3>

                    {results.map((result) => (
                        <div key={result.id} className="search-result">
                            <h4>{result.name}</h4>
                            <p>{result.address}</p>
                            <p>System: {getSystemName(result.system_type)}</p>
                            {result.equipment && (
                                <p>Equipment: {result.equipment.name}</p>
                            )}
                            <div className="result-actions">
                                <button onClick={() => onBuildingSelected(result)}>
                                    View Building
                                </button>
                                {result.equipment && (
                                    <button onClick={() => onEquipmentSelected(result.equipment)}>
                                        View Equipment
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
```

---

## 🚀 **Implementation Roadmap**

### **Phase 1: Core URL System (Weeks 1-3)**
- [ ] Implement URL shortening service for all building systems
- [ ] Build view mapping system with system-specific configurations
- [ ] Create access control framework
- [ ] Develop basic analytics across all systems

### **Phase 2: NFC Framework (Weeks 4-6)**
- [ ] Implement NFC data generation for all building systems
- [ ] Build tap handling system with system-specific information
- [ ] Create tag management interface
- [ ] Add NFC analytics for different system types

### **Phase 3: Hub Search (Weeks 7-9)**
- [ ] Build search engine with system-specific filtering
- [ ] Implement geolocation services
- [ ] Create building directory with system information
- [ ] Add public/private controls for all systems

### **Phase 4: Integration & Polish (Weeks 10-12)**
- [ ] Integrate all three systems across all building systems
- [ ] Add comprehensive analytics for each system type
- [ ] Implement security features
- [ ] Performance optimization for system-specific queries

---

## 🎯 **Success Metrics**

### **Adoption Metrics (By System Type)**
- **Electrical**: > 70% of electrical contractors create site URLs
- **HVAC**: > 60% of HVAC technicians create site URLs
- **Plumbing**: > 50% of plumbing contractors create site URLs
- **Fire Protection**: > 80% of fire protection technicians create site URLs
- **Security**: > 65% of security technicians create site URLs
- **Overall**: > 60% of users create at least one site URL

### **Usage Metrics (By System Type)**
- **URL Access Rate**: > 70% of created URLs are accessed within 30 days
- **NFC Tap Rate**: > 50% of NFC tags are tapped within 30 days
- **Search Success Rate**: > 85% of searches return relevant results
- **System-Specific Search**: > 90% accuracy for system-specific queries

### **Performance Metrics**
- **URL Resolution Time**: < 200ms average across all systems
- **NFC Tap Response**: < 500ms average across all systems
- **Search Response Time**: < 300ms average for system-specific searches

This comprehensive architecture now supports **all building systems** with system-specific configurations, equipment tracking, and specialized search capabilities! 🚀
