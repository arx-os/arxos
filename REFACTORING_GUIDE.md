# ArxOS Refactoring Guide

## 🎯 Purpose

This guide provides step-by-step instructions for refactoring the ArxOS codebase to eliminate technical debt, following industry best practices.

---

## 📋 Phase 1: Refactor `render3d/renderer.rs` (PRIORITY 1)

### Current State
- **File:** `src/render3d/renderer.rs`
- **Size:** 1,090 LOC (40KB)
- **Methods:** 39 methods
- **Issue:** God Object anti-pattern

### Target State
- **Main file:** `src/render3d/renderer.rs` (~300 LOC)
- **New modules:** 6 supporting modules (~700 LOC total)
- **Methods:** 10-15 core methods in main, rest distributed

---

## 🛠️ Step-by-Step Refactoring Plan

### Prerequisites (30 minutes)

1. **Create feature branch:**
   ```bash
   cd /Users/joelpate/repos/arxos
   git checkout -b refactor/render3d-modularization
   ```

2. **Run baseline tests:**
   ```bash
   cargo test --features render3d 2>&1 | tee baseline_tests.log
   ```

3. **Document current behavior:**
   ```bash
   # Generate API documentation
   cargo doc --no-deps --open

   # Save current renderer API
   grep "pub fn" src/render3d/renderer.rs > renderer_api_baseline.txt
   ```

---

### Step 1: Extract View Renderers (2 hours)

**Goal:** Extract 6 view-specific rendering methods → `views/` module

**Files to Create:**
- `src/render3d/views/mod.rs`
- `src/render3d/views/isometric.rs`
- `src/render3d/views/orthographic.rs`
- `src/render3d/views/perspective.rs`
- `src/render3d/views/planar.rs` (top-down, front, side)

**Methods to Extract:**
1. `render_isometric_view()` - 50 LOC
2. `render_orthographic_view()` - 40 LOC
3. `render_perspective_view()` - 55 LOC
4. `render_top_down_view()` - 40 LOC
5. `render_front_view()` - 36 LOC
6. `render_side_view()` - 36 LOC

**Total reduction:** ~257 LOC

#### 1.1 Create views/mod.rs

```rust
// src/render3d/views/mod.rs

//! View-specific rendering for different projection types

use super::types::*;
use crate::core::EquipmentStatus;

pub mod isometric;
pub mod orthographic;
pub mod perspective;
pub mod planar;

pub use isometric::render_isometric_view;
pub use orthographic::render_orthographic_view;
pub use perspective::render_perspective_view;
pub use planar::{render_top_down_view, render_front_view, render_side_view};

/// View renderer trait for consistency
pub trait ViewRenderer {
    fn render(&self, scene: &Scene3D, projection: &Projection3D) -> Result<String, Box<dyn std::error::Error>>;
}
```

#### 1.2 Extract isometric view

**File:** `src/render3d/views/isometric.rs`

```rust
//! Isometric view rendering

use super::*;

/// Render scene in isometric view
pub fn render_isometric_view(scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
    let mut output = String::new();

    output.push_str("📐 Isometric 3D View:\n");
    output.push_str("┌─────────────────────────────────────────────────────────────┐\n");

    // Sort floors by level for proper rendering order
    let mut floors = scene.floors.clone();
    floors.sort_by_key(|f| f.level);

    for floor in &floors {
        output.push_str(&format!(
            "│ Floor {}: {} (Z: {:.1}m) │\n",
            floor.level,
            floor.name.as_str(),
            floor.elevation
        ));

        // Show equipment on this floor
        let floor_equipment: Vec<&Equipment3D> = scene
            .equipment
            .iter()
            .filter(|e| e.floor_level == floor.level)
            .collect();

        for equipment in &floor_equipment {
            let status_symbol = match equipment.status {
                EquipmentStatus::Active => "🟢",
                EquipmentStatus::Maintenance => "🟡",
                EquipmentStatus::OutOfOrder => "🔴",
                EquipmentStatus::Inactive | EquipmentStatus::Unknown => "⚪",
            };
            output.push_str(&format!(
                "│   {} {} at ({:.1}, {:.1}, {:.1}) │\n",
                status_symbol,
                equipment.name.as_str(),
                equipment.position.x,
                equipment.position.y,
                equipment.position.z
            ));
        }
    }

    output.push_str("└─────────────────────────────────────────────────────────────┘\n");

    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_render_isometric_view() {
        // TODO: Add test with sample Scene3D
    }
}
```

#### 1.3 Update renderer.rs

**In `src/render3d/renderer.rs`:**

```rust
// Add import
use super::views;

// Replace method implementation:
fn render_isometric_view(&self, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
    views::render_isometric_view(scene)
}
```

#### 1.4 Test

```bash
cargo build --features render3d
cargo test --features render3d
```

#### 1.5 Commit

```bash
git add src/render3d/views/
git add src/render3d/renderer.rs
git commit -m "refactor(render3d): extract isometric view to views module

- Create views/isometric.rs with render_isometric_view()
- Keep API stable in renderer.rs (delegates to views module)
- No functional changes, pure code organization
- Tests pass"
```

**Repeat for other view renderers (orthographic, perspective, planar)**

---

### Step 2: Extract Transform Operations (1.5 hours)

**Goal:** Extract transformation methods → `transforms.rs`

**Methods to Extract:**
1. `transform_floors_3d()` - 20 LOC
2. `transform_equipment_3d()` - 25 LOC
3. `transform_rooms_3d()` - 20 LOC
4. `transform_point()` - 10 LOC
5. `transform_bounding_box()` - 12 LOC

**Total reduction:** ~87 LOC

#### 2.1 Create transforms.rs

```rust
// src/render3d/transforms.rs

//! 3D transformation operations for rendering

use super::types::*;
use crate::spatial::{BoundingBox3D, Point3D};

/// Transform floors for rendering
pub fn transform_floors(floors: &[Floor3D], camera: &Camera3D, projection: &Projection3D) -> Vec<Floor3D> {
    floors
        .iter()
        .map(|f| {
            let mut transformed = f.clone();
            transformed.bounding_box = transform_bounding_box(&f.bounding_box, camera, projection);
            transformed
        })
        .collect()
}

/// Transform equipment for rendering
pub fn transform_equipment(equipment: &[Equipment3D], camera: &Camera3D, projection: &Projection3D) -> Vec<Equipment3D> {
    equipment
        .iter()
        .map(|e| {
            let mut transformed = e.clone();
            transformed.position = transform_point(&e.position, camera, projection);
            transformed.bounding_box = transform_bounding_box(&e.bounding_box, camera, projection);
            transformed
        })
        .collect()
}

/// Transform a 3D point through camera and projection
pub fn transform_point(point: &Point3D, camera: &Camera3D, projection: &Projection3D) -> Point3D {
    // Camera transform
    let view_x = point.x - camera.position.x;
    let view_y = point.y - camera.position.y;
    let view_z = point.z - camera.position.z;

    // Projection transform (simplified - actual impl in renderer.rs)
    match projection.projection_type {
        ProjectionType::Isometric => isometric_transform(view_x, view_y, view_z),
        ProjectionType::Orthographic => orthographic_transform(view_x, view_y, view_z),
        ProjectionType::Perspective => perspective_transform(view_x, view_y, view_z, camera),
    }
}

fn isometric_transform(x: f64, y: f64, z: f64) -> Point3D {
    Point3D {
        x: (x - y) * 0.866, // cos(30°)
        y: (x + y) * 0.5 - z,
        z: 0.0,
    }
}

// ... other transform functions

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_transform_point() {
        // TODO: Test transformations
    }
}
```

#### 2.2 Update renderer.rs

```rust
use super::transforms;

fn transform_floors_3d(&self, floors: &[Floor3D]) -> Vec<Floor3D> {
    transforms::transform_floors(floors, &self.camera, &self.projection)
}
```

---

### Step 3: Extract Spatial Query Methods (1 hour)

**Goal:** Extract spatial query methods → `spatial_query.rs`

**Methods:**
1. `query_spatial_entities()` - 8 LOC
2. `query_entities_within_radius()` - 13 LOC
3. `query_entities_in_room()` - 19 LOC
4. `query_entities_on_floor()` - 19 LOC
5. `find_nearest_entity()` - 9 LOC
6. `get_equipment_clusters()` - 23 LOC

**Total reduction:** ~91 LOC

#### 3.1 Create spatial_query.rs

```rust
// src/render3d/spatial_query.rs

//! Spatial query operations for 3D renderer

use crate::ifc::{SpatialIndex, SpatialQueryResult};
use crate::spatial::{BoundingBox3D, Point3D};

pub struct SpatialQueryHelper<'a> {
    spatial_index: &'a SpatialIndex,
}

impl<'a> SpatialQueryHelper<'a> {
    pub fn new(spatial_index: &'a SpatialIndex) -> Self {
        Self { spatial_index }
    }

    /// Get entities within a 3D bounding box
    pub fn entities_in_bbox(&self, bbox: &BoundingBox3D) -> Vec<SpatialQueryResult> {
        self.spatial_index.find_within_bounding_box(bbox.clone())
    }

    /// Get entities within radius of a point
    pub fn entities_within_radius(&self, center: &Point3D, radius: f64) -> Vec<SpatialQueryResult> {
        self.spatial_index.find_within_radius(center.clone(), radius)
    }

    // ... other methods
}
```

---

### Step 4: Consolidate Projection Methods (1 hour)

**Goal:** Move projection methods to `projection.rs` module

**Methods:**
1. `isometric_projection()` - 5 LOC
2. `orthographic_projection()` - 5 LOC
3. `perspective_projection()` - 5 LOC
4. `project_to_screen()` - 23 LOC

**Total reduction:** ~38 LOC

#### 4.1 Add to existing projection.rs

```rust
// src/render3d/projection.rs

impl Projection3D {
    pub fn project_point(&self, point: &Point3D) -> Point3D {
        match self.projection_type {
            ProjectionType::Isometric => self.isometric(point),
            ProjectionType::Orthographic => self.orthographic(point),
            ProjectionType::Perspective => self.perspective(point),
        }
    }

    pub fn isometric(&self, point: &Point3D) -> Point3D {
        Point3D {
            x: (point.x - point.y) * 0.866,
            y: (point.x + point.y) * 0.5 - point.z,
            z: 0.0,
        }
    }

    // ... other projection methods
}
```

---

### Step 5: Final Cleanup (30 minutes)

1. **Remove extracted code** from renderer.rs
2. **Update imports**
3. **Run full test suite**
4. **Update documentation**

```bash
cargo test
cargo doc --no-deps
cargo clippy -- -W clippy::all
```

---

## 📊 Expected Results

### Before
```
src/render3d/renderer.rs: 1,090 LOC, 39 methods
```

### After
```
src/render3d/
├── renderer.rs: ~520 LOC, 15 methods (core orchestration)
├── views/
│   ├── mod.rs: 30 LOC
│   ├── isometric.rs: 50 LOC
│   ├── orthographic.rs: 45 LOC
│   ├── perspective.rs: 60 LOC
│   └── planar.rs: 75 LOC
├── transforms.rs: 120 LOC
├── spatial_query.rs: 110 LOC
└── projection.rs: 80 LOC (enhanced)

Total: Same functionality, better organization
Largest file: 520 LOC (52% reduction from 1,090)
```

---

## ✅ Success Criteria

- [ ] All existing tests pass
- [ ] No changes to public API
- [ ] Renderer.rs < 600 LOC
- [ ] No file > 200 LOC in new modules
- [ ] Documentation updated
- [ ] Clippy warnings addressed

---

## 🧪 Testing Strategy

### After Each Extraction

```bash
# Build check
cargo build --features render3d

# Run specific tests
cargo test --features render3d renderer

# Check for regressions
cargo test --all-features

# Verify public API unchanged
cargo doc --no-deps && diff renderer_api_baseline.txt <(grep "pub fn" src/render3d/renderer.rs)
```

### Before Merging

```bash
# Full test suite
cargo test --all-features

# Performance check (should be same)
cargo build --release
# Run performance benchmark if available

# Code quality
cargo clippy -- -D warnings
cargo fmt -- --check
```

---

## 🚀 Phase 2: build_hierarchy() (279 LOC → ~100 LOC)

After completing renderer.rs refactoring, proceed with:

**File:** `src/ifc/hierarchy/builder.rs`
**Method:** `build_hierarchy()` - 279 lines (God function)

### Refactoring Steps:

1. **Extract storey extraction** → `extract_storeys()`
2. **Extract space extraction** → `extract_spaces()`
3. **Extract equipment extraction** → `extract_equipment()`
4. **Extract hierarchy assembly** → `assemble_building()`
5. **Extract reference resolution** → `resolve_references()`

### Expected Result:
```rust
pub fn build_hierarchy(&self) -> Result<Building, Box<dyn std::error::Error>> {
    // High-level orchestration (~50 lines)
    let storeys = self.extract_storeys()?;
    let spaces = self.extract_spaces()?;
    let equipment = self.extract_equipment()?;

    self.resolve_references(&storeys, &spaces, &equipment)?;

    self.assemble_building(storeys, spaces, equipment)
}

// Each extracted method: 40-50 lines
fn extract_storeys(&self) -> Result<Vec<Floor>> { ... }
fn extract_spaces(&self) -> Result<Vec<Room>> { ... }
fn extract_equipment(&self) -> Result<Vec<Equipment>> { ... }
fn resolve_references(...) -> Result<()> { ... }
fn assemble_building(...) -> Result<Building> { ... }
```

---

## 📈 Metrics Tracking

Track progress using:

```bash
# LOC per file
tokei src/render3d/

# Method count
grep -c "pub fn\|fn " src/render3d/renderer.rs

# Complexity (requires cargo-geiger)
cargo install cargo-geiger
cargo geiger
```

---

## 🎯 Long-Term Goals

1. **No files >600 LOC** (current: 4 files >800 LOC)
2. **No functions >100 lines** (current: 10 functions >100 lines)
3. **Average module size <400 LOC**
4. **Test coverage >90%**

---

## 📚 References

- [Refactoring Guru - God Object](https://refactoring.guru/smells/large-class)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Clean Code Principles](https://github.com/ryanmcdermott/clean-code-javascript)

---

## 🤝 Contributing

When refactoring:
1. ✅ One logical change per commit
2. ✅ Tests pass after each commit
3. ✅ Public API remains stable
4. ✅ Documentation updated
5. ✅ No performance regressions

---

**Last Updated:** 2025-01-15
**Status:** Ready for implementation
**Estimated Total Time:** 1 week (1 developer)
