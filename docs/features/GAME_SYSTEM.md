# Gamified PR Review & Planning System

**Last Updated:** November 2025  
**Status:** ✅ Complete (Core Features)

---

## Overview

The Gamified PR Review & Planning System transforms building data management into an interactive, game-like experience in the terminal. Power users can review contractor PRs, plan equipment placement, and learn from historical scenarios—all with real-time constraint validation and 3D visualization.

## Key Features

### 🎮 Game Modes

1. **PR Review Mode** - Review contractor PRs with constraint validation
2. **Planning Mode** - Interactive equipment placement with real-time feedback
3. **Learning Mode** - Educational scenarios from historical PRs

### ✨ Core Capabilities

- **Constraint Validation** - Spatial, structural, code, budget, and accessibility checks
- **3D Visualization** - Minecraft-like ASCII art rendering in terminal
- **IFC Compatibility** - Full round-trip support with metadata preservation
- **Real-time Feedback** - Instant validation as equipment is placed
- **PR Export** - Export planning sessions as reviewable PRs

---

## Quick Start

### Review a PR

```bash
# Basic review
arx game review --pr-id pr_001 --building "My Building"

# Interactive review with 3D visualization
arx game review --pr-id pr_001 --building "My Building" --interactive

# Review and export to IFC
arx game review --pr-id pr_001 --building "My Building" --export-ifc output.ifc
```

### Plan Equipment Placement

```bash
# Interactive planning session
arx game plan --building "My Building" --interactive

# Plan and export as PR
arx game plan --building "My Building" --interactive --export-pr ./prs/my_plan

# Plan and export to IFC
arx game plan --building "My Building" --interactive --export-ifc plan.ifc
```

### Learn from Historical PRs

```bash
# Load and study a historical PR
arx game learn --pr-id pr_approved_001 --building "My Building"
```

---

## Architecture

### Module Structure

```
crates/arxos/crates/arxos/src/game/
├── mod.rs           # Public API and re-exports
├── types.rs         # Core game types (GameMode, GameScenario, etc.)
├── scenario.rs      # Scenario loading from PRs and buildings
├── state.rs         # Game state management (score, progress, stats)
├── constraints.rs   # Constraint validation system
├── pr_game.rs       # PR review game mode
├── planning.rs      # Planning game mode
├── ifc_sync.rs      # IFC metadata preservation
├── ifc_mapping.rs   # EquipmentType ↔ IFC entity type mapping
└── export.rs        # IFC export from game state
```

### Key Components

#### Constraint System

Validates equipment placements against:
- **Structural** - Wall support areas, load capacity
- **Spatial** - Clearance requirements, proximity rules
- **Code** - Building code compliance (ADA, fire safety, etc.)
- **Budget** - Cost constraints
- **User Preferences** - Teacher/occupant requests

Constraints are loaded from YAML files:

```yaml
constraints:
  structural:
    - type: wall_support
      floor: 0
      valid_areas:
        - bbox:
            min: {x: 5.0, y: 5.0, z: 0.0}
            max: {x: 15.0, y: 15.0, z: 3.0}
          load_capacity: 50.0  # kg
      notes: "Concrete wall support required"
  spatial:
    - type: clearance
      min_clearance: 0.5  # meters
      equipment_type: "Electrical"
  code:
    - type: "ADA"
      requirement: "Accessibility compliance required"
      is_mandatory: true
```

#### IFC Sync Layer

Preserves IFC metadata throughout game operations:
- Original IFC entity IDs
- IFC entity types
- Placement chain references
- Original IFC properties

This ensures complete round-trip compatibility—equipment placed in the game can be exported back to IFC with all metadata intact.

---

## Workflows

### PR Review Workflow

1. Contractor submits PR with AR scan data (`markup.json`)
2. Power user loads PR: `arx game review --pr-id pr_001 --building "Building"`
3. System validates all equipment against constraints
4. Review summary shows:
   - Total items
   - Valid vs. invalid placements
   - Violations by severity
   - Critical issues that must be addressed
5. Interactive review allows:
   - 3D navigation to inspect placements
   - Real-time constraint checking
   - Approve/Reject/RequestChanges decisions
6. Approved PRs can be exported to IFC for integration

### Planning Workflow

1. Start planning session: `arx game plan --building "Building" --interactive`
2. Navigate building in 3D terminal view
3. Place equipment with keyboard controls:
   - Select equipment type
   - Position in 3D space
   - Real-time validation feedback
4. System validates each placement:
   - Structural support
   - Spatial clearance
   - Code compliance
   - Budget constraints
5. Export completed plan:
   - As PR for review: `--export-pr ./prs/my_plan`
   - Direct to IFC: `--export-ifc plan.ifc`

### Learning Workflow

1. Load historical PR: `arx game learn --pr-id pr_approved_001 --building "Building"`
2. Study equipment placements in 3D
3. Review constraint validations
4. Understand expert decisions and best practices

---

## Constraint Types

### Structural Constraints

- **Wall Support Areas** - Valid mounting locations with load capacity
- **Floor Load Limits** - Maximum weight per area
- **Mounting Requirements** - Specific mounting point requirements

### Spatial Constraints

- **Minimum Clearance** - Required space around equipment
- **Maximum Proximity** - Distance limits between equipment
- **Access Routes** - Required paths for maintenance

### Code Constraints

- **ADA Compliance** - Accessibility requirements
- **Fire Safety** - Exit paths, sprinkler clearances
- **Building Codes** - Local code compliance

### Budget Constraints

- **Cost Limits** - Maximum budget per project/area
- **Cost Per Item** - Equipment cost tracking

---

## IFC Compatibility

### Metadata Preservation

The game system preserves all IFC metadata:

- **Entity IDs** - Original `#123` style IDs maintained
- **Entity Types** - `IFCLIGHTFIXTURE`, `IFCAIRTERMINAL`, etc.
- **Placement Chains** - Parent placement references
- **Properties** - All original IFC properties

### Type Mapping

Equipment types automatically map to IFC entities:

| EquipmentType | IFC Entity Type |
|---------------|----------------|
| HVAC | `IFCAIRTERMINAL` |
| Electrical | `IFCLIGHTFIXTURE` |
| Plumbing | `IFCFLOWTERMINAL` |
| Network | `IFCCABLECARRIERSEGMENT` |
| Furniture | `IFCFURNISHINGELEMENT` |
| Safety | `IFCDISTRIBUTIONELEMENT` |

For game-created equipment, synthetic IFC IDs are generated (starting from `#10000`).

### Round-Trip Workflow

1. **Import IFC** → Equipment with IFC metadata
2. **Game Operations** → Metadata preserved through all operations
3. **Export IFC** → Complete metadata restored, valid IFC file

---

## Game Overlay

The interactive 3D renderer displays a game overlay showing:

```
╔════════════════════════════════════════════════════════════╗
║                    GAME OVERLAY                           ║
╠════════════════════════════════════════════════════════════╣
║ Objective: Review PR pr_001: 3 equipment items            ║
║ Progress: [================================================] ║
║ Score: 250                                                  ║
║ Valid: 2 / 3 | Violations: 1                               ║
╚════════════════════════════════════════════════════════════╝
```

### Overlay Elements

- **Objective** - Current game objective
- **Progress Bar** - Completion percentage
- **Score** - Current score based on validations
- **Validation Status** - Valid/invalid counts, violation summary

---

## Examples

### Example: Newline Interactive Boards Deployment

A school district needs to deploy interactive boards in classrooms with:
- Teacher preference constraints (specific locations)
- Structural constraints (wall support only)
- Budget constraints (cost per room)

**Solution:**
1. Load building: `arx game plan --building "School District" --interactive`
2. Navigate to each classroom
3. Place boards with real-time validation
4. System validates:
   - Position has wall support
   - Meets teacher preference zones
   - Within budget constraints
5. Export plan as PR for approval
6. Once approved, export to IFC for installer use

### Example: PR Review for Contractor Markups

Contractor submits PR with 10 light fixtures from AR scan:

```bash
arx game review --pr-id contractor_pr_001 --building "Office Building" --interactive
```

System identifies:
- 8 fixtures valid (correct locations, proper clearance)
- 2 fixtures have violations:
  - Fixture #5: Insufficient clearance (0.3m, requires 0.5m)
  - Fixture #8: Not in wall support area

Reviewer can:
- Request changes for violations
- Approve valid fixtures
- Suggest alternative positions
- Export approved items to IFC

---

## Best Practices

### Constraint Files

1. **Organize by building** - `{building_name}-constraints.yaml`
2. **Document constraints** - Include notes explaining requirements
3. **Version control** - Track constraint changes in Git
4. **Test constraints** - Validate against known good placements

### PR Structure

PRs should follow standard structure:
```
prs/
  └── pr_{timestamp}_{user_id}/
      ├── metadata.yaml      # PR metadata
      ├── markup.json        # AR scan data + equipment
      └── README.md          # Human-readable summary
```

### Game State Management

- Validate frequently during planning
- Check constraint violations before export
- Use interactive mode for complex placements
- Export to PR for review before final IFC export

---

## Troubleshooting

### Common Issues

**"PR directory not found"**
- Ensure PR directory exists at `./prs/pr_{id}` or specify with `--pr-dir`

**"Building not found"**
- Verify `building.yaml` exists in current directory
- Check building name matches exactly

**"Constraint validation fails unexpectedly"**
- Check constraints file format
- Verify coordinate systems match
- Ensure bounding boxes are correctly defined

**"IFC export has missing metadata"**
- Verify IFC sync manager is used
- Check equipment has IFC metadata in properties
- Use `apply_ifc_type_mapping` for game-created equipment

---

## Related Documentation

- **[AR Terminal Design](./../ar/AR_TERMINAL_DESIGN.md)** - Mobile AR + Terminal integration
- **[IFC Processing](./IFC_PROCESSING.md)** - IFC import/export details
- **[Mobile FFI Integration](./../mobile/MOBILE_FFI_INTEGRATION.md)** - Mobile app integration

---

## Future Enhancements

- [ ] Enhanced learning mode with expert commentary
- [ ] Multi-player collaborative planning
- [ ] Advanced constraint visualizations
- [ ] Automated constraint suggestions
- [ ] Integration with BIM software APIs

