# IFC Compatibility

**Last Updated:** November 2025

---

## Overview

The game system maintains complete IFC compatibility through metadata preservation and proper type mapping. Equipment placed or modified in game modes can be exported back to IFC files with all original metadata intact.

---

## Metadata Preservation

### Preserved Elements

- **IFC Entity IDs** - Original `#123` format IDs
- **IFC Entity Types** - `IFCLIGHTFIXTURE`, `IFCAIRTERMINAL`, etc.
- **Placement Chains** - Parent placement references (`#10`, `#20`)
- **Original Properties** - All IFC property sets and values
- **Coordinate Systems** - IFC coordinate system information

### Synthetic IDs

For game-created equipment (not from IFC import), synthetic IFC IDs are generated:
- Starting from `#10000`
- Incremental assignment
- Guaranteed unique within session
- Stored in equipment properties for future reference

---

## Type Mapping

### EquipmentType → IFC Entity Types

| ArxOS EquipmentType | IFC Entity Type | Notes |
|---------------------|-----------------|-------|
| HVAC | `IFCAIRTERMINAL` | Default for HVAC equipment |
| Electrical | `IFCLIGHTFIXTURE` | Lights, fixtures, lamps |
| Plumbing | `IFCFLOWTERMINAL` | Faucets, valves, fixtures |
| Network | `IFCCABLECARRIERSEGMENT` | Network infrastructure |
| Furniture | `IFCFURNISHINGELEMENT` | Furniture items |
| Safety | `IFCDISTRIBUTIONELEMENT` | Safety equipment (generic) |
| AV | `IFCDISTRIBUTIONELEMENT` | Audio/visual equipment |

### Smart Type Detection

The mapper uses equipment name patterns for refinement:
- `*light*`, `*lamp*`, `*fixture*` → `IFCLIGHTFIXTURE`
- `*air*`, `*vent*`, `*hvac*` → `IFCAIRTERMINAL`
- `*pump*` → `IFCPUMP`
- `*fan*` → `IFCFAN`
- `*board*`, `*panel*` → `IFCELECTRICDISTRIBUTIONBOARD`

---

## Round-Trip Workflow

### Import → Game → Export

1. **Import IFC** - Equipment loaded with full IFC metadata
2. **Game Operations** - Metadata preserved through all actions:
   - Moving equipment
   - Adding new equipment
   - Modifying properties
3. **Export IFC** - All metadata restored:
   - Original entity IDs maintained
   - Placement chains preserved
   - Properties merged correctly

### Example

```rust
// Import equipment from IFC
let equipment = load_from_ifc("building.ifc");

// Equipment has IFC metadata in properties:
// - ifc_entity_id: "#123"
// - ifc_entity_type: "IFCLIGHTFIXTURE"
// - ifc_placement_chain: "#10,#20"

// Use in game
planning_game.place_equipment(...);
planning_game.move_equipment(...);

// Export - metadata preserved
export_game_to_ifc(game_state, "output.ifc");

// Output IFC contains:
// #123=IFCLIGHTFIXTURE('...', '...', $, #20);
// With all original properties and placement chains
```

---

## Coordinate System Consistency

The system maintains coordinate system information:

- **IFC Coordinates** - Original IFC coordinate system
- **Building Local** - Transformed to building-local coordinates for game
- **Export** - Coordinates preserved correctly for IFC export

Transformations are tracked and reversed during export.

---

## Validation

### IFC Entity Type Validation

The system validates that generated IFC entity types are valid IFC4 entities:

```rust
IFCTypeMapper::validate_ifc_entity_type("IFCLIGHTFIXTURE")  // ✅ true
IFCTypeMapper::validate_ifc_entity_type("INVALID_TYPE")     // ❌ false
```

Valid types include:
- `IFCAIRTERMINAL`, `IFCLIGHTFIXTURE`, `IFCFLOWTERMINAL`
- `IFCPUMP`, `IFCFAN`, `IFCVALVE`
- `IFCELECTRICDISTRIBUTIONBOARD`
- `IFCDISTRIBUTIONELEMENT` (generic fallback)

---

## Best Practices

1. **Preserve Original Metadata** - Never discard IFC metadata
2. **Use Valid Types** - Always validate IFC entity types
3. **Track Changes** - Log metadata modifications for audit
4. **Test Round-Trip** - Verify export/import cycle preserves data
5. **Document Mapping** - Record custom type mappings

---

## Troubleshooting

**"IFC export missing entity IDs"**
- Ensure IFC sync manager is used
- Check equipment properties contain `ifc_entity_id`
- Use `get_or_create_metadata()` for game-created equipment

**"Invalid IFC entity type"**
- Verify type mapping with `validate_ifc_entity_type()`
- Check EquipmentType matches expected values
- Use generic `IFCDISTRIBUTIONELEMENT` as fallback

**"Placement chains lost"**
- Preserve placement chains in IFC metadata
- Don't modify `ifc_placement_chain` property
- Use sync manager to track changes

