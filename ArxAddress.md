# ArxOS Address System — Full Specification for Cursor

**Goal**: Implement the **ArxOS Address** — a hierarchical, file-path-style naming system that is:
- **Globally unique**
- **Human + machine readable**
- **Standardized for 14 core building systems**
- **Open for custom items (e.g., PB&J sandwich)**
- **Backwards compatible**
- **No breaking changes**

---

## 1. Address Format
/<country>/<state>/<city>/<building>/<floor>/<room>/<fixture>

### Example (Standardized): /usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01

### Example (Custom): /usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge/pbj-sandwich

---

## 2. Core 14 Standardized Systems (Reserved)

```rust
const RESERVED_SYSTEMS: [&str; 14] = [
    "hvac",         // boilers, AHUs
    "plumbing",     // valves, pumps
    "electrical",   // panels, breakers
    "fire",         // sprinklers, alarms
    "lighting",     // fixtures, controls
    "security",     // cameras, access
    "elevators",    // cars, controls
    "roof",         // units, drains
    "windows",      // frames, glass
    "doors",        // hinges, locks
    "structure",    // columns, beams
    "envelope",     // walls, insulation
    "it",           // switches, APs
    "furniture",    // desks, chairs
];

---

## 3. ArxAddress Struct (src/domain/address.rs)
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct ArxAddress {
    pub path: String,
}

impl ArxAddress {
    pub fn new(
        country: &str, state: &str, city: &str,
        building: &str, floor: &str, room: &str, fixture: &str,
    ) -> Self {
        let path = format!("/{country}/{state}/{city}/{building}/{floor}/{room}/{fixture}");
        Self { path }
    }

    pub fn from_path(path: &str) -> Result<Self> {
        let clean = path.trim_start_matches('/');
        let parts: Vec<&str> = clean.split('/').collect();
        if parts.len() != 7 {
            bail!("ArxAddress must have 7 parts: {path}")
        }
        Ok(Self { path: format!("/{}", clean) })
    }

    pub fn validate(&self) -> Result<()> {
        let parts: Vec<&str> = self.path.trim_start_matches('/').split('/').collect();
        let system = parts[5]; // 6th part = room/system

        if RESERVED_SYSTEMS.contains(&system) {
            let fixture = parts[6];
            match system {
                "hvac" => if !fixture.starts_with("boiler-") && !fixture.starts_with("ahu-") { bail!("HVAC fixture must be boiler-XX or ahu-XX") },
                "plumbing" => if !fixture.starts_with("valve-") && !fixture.starts_with("pump-") { bail!("Plumbing fixture must be valve-XX or pump-XX") },
                "electrical" => if !fixture.starts_with("panel-") && !fixture.starts_with("breaker-") { bail!("Electrical fixture must be panel-XX or breaker-XX") },
                // ... add others
                _ => {}
            }
        }
        // Open systems: anything goes
        Ok(())
    }

    pub fn parent(&self) -> String {
        let parts: Vec<&str> = self.path.trim_start_matches('/').split('/').collect();
        format!("/{}", parts[..6].join("/"))
    }
}

---

## 4. Update Fixture Struct (src/domain/fixture.rs)
pub struct Fixture {
    pub address: ArxAddress,
    pub type_: String,
    pub model: Option<String>,
    pub install_date: Option<String>,
    pub grid: Option<String>,
    pub coords: Option<Coord>,
    pub notes: Option<String>,
}

---

## 5. Update building.yaml Schema
# Standardized
- address: /usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01
  type: boiler
  model: Lochinvar KNIGHT-199
  grid: D-4
  coords: { x: 12.3, y: 4.1, z: 0.0 }

# Custom
- address: /usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge/pbj-sandwich
  type: food
  notes: "For Mr. Johnson"

  ---

  ## 6. CLI: arx add --at /path
  // src/cli/add.rs
let address = if let Some(path) = matches.get_one::<String>("at") {
    ArxAddress::from_path(path)?
} else {
    // Auto-generate from context
    let building = get_current_building()?; // from .arxos/config
    let floor = get_current_floor()?;
    let room = infer_room_from_grid(grid)?;
    ArxAddress::new("usa", "ny", "brooklyn", &building, &floor, &room, &next_fixture_id(&room)?)
};
address.validate()?;

---

## 7. Auto-Generate Address from Grid
// src/grid/to_address.rs
pub fn grid_to_address(grid: &str, floor: &str, building: &str) -> ArxAddress {
    let room = match grid {
        "D-4" => "mech",
        "C-8" => "kitchen",
        _ => "unknown-room",
    };
    let fixture_type = "boiler"; // from CLI
    let id = next_id_in_room(room, fixture_type);
    ArxAddress::new("usa", "ny", "brooklyn", building, floor, room, &format!("{fixture_type}-{id:02}"))
}

---

## 8. IFC Sync: Path → GUID
// src/adapters/ifc/sync.rs
let guid = blake3::hash(address.path.as_bytes()).to_hex().to_string();
model.create_entity("IfcBoiler", &guid, &fixture.model, coords)?;

---

## 9. Query Engine
// src/query/mod.rs
pub fn query(path_glob: &str) -> Vec<Fixture> {
    glob::glob(&format!(".arxos/repos{}/*.yaml", path_glob))
        .map(|p| load_fixture(p))
        .collect()
}

arx query "/usa/ny/*/floor-*/mech/boiler-*"
arx query "/ps-118/floor-02/kitchen/fridge/*"

---

## 10. Backwards Compatibility

Old building.yaml without address → ignored
arx add without --at → auto-generates
arx list → shows address if present

---

Patch Summary
+ src/domain/address.rs
+ src/grid/to_address.rs
+ Update Fixture struct
+ Update CLI --at
+ Update IFC sync
+ Update query engine
+ Add RESERVED_SYSTEMS

