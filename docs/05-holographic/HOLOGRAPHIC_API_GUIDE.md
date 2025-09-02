# Holographic ArxObject API Guide
**Version:** 1.0  
**Module:** `arxos_core::holographic`

## Overview

The Holographic ArxObject system transforms the basic 13-byte ArxObject into an infinitely fractal holographic seed capable of procedurally generating reality at any scale. This guide covers Phase 1 implementation: Enhanced Procedural Generation.

## Quick Start

```rust
use arxos_core::holographic::prelude::*;
use arxos_core::holographic::{
    fractal::FractalSpace,
    noise::fractal_noise_3d,
    lsystem::ArchitecturalLSystem,
    automata::CellularAutomaton3D,
};

// Create a fractal coordinate
let coord = FractalCoordinate::from_mm(5000); // 5 meters

// Generate procedural noise
let noise = fractal_noise_3d(
    42,     // seed
    1.5,    // x
    2.5,    // y
    3.5,    // z
    4,      // octaves
    0.5,    // persistence
    2.0,    // lacunarity
);

// Create architectural structures with L-Systems
let arch = ArchitecturalLSystem::new(
    ArchitecturePattern::Tower,
    building_id,
    seed,
);
let objects = arch.generate_objects(3, (5000, 5000, 0));

// Simulate dynamic systems with cellular automata
let mut automaton = CellularAutomaton3D::random(
    10, 10, 10,              // dimensions
    AutomatonRules::conway_3d(),
    0.3,                     // initial density
    seed,
);
automaton.evolve(10);
let objects = automaton.to_arxobjects(building_id, (0, 0, 0), 100);
```

## Module Components

### 1. Fractal Coordinate System (`holographic::fractal`)

Provides infinite-precision coordinates using fractal mathematics.

#### FractalCoordinate

```rust
/// Fractal coordinate with infinite precision
pub struct FractalCoordinate {
    pub base: u16,        // Base coordinate in mm
    pub depth: i8,        // Fractal depth (zoom level)
    pub sub_position: f32, // Sub-voxel position
}

// Example: Zooming in and out
let mut coord = FractalCoordinate::from_mm(1000);
coord.rescale(2);  // Zoom in 2 levels (9x magnification)
coord.rescale(-1); // Zoom out 1 level (3x reduction)

// Convert to absolute position
let position = coord.to_absolute(1.0); // Scale factor
```

#### FractalSpace

```rust
/// 3D fractal space position
let space = FractalSpace::from_mm(1000, 2000, 3000);

// Calculate distance
let other = FractalSpace::from_mm(1500, 2500, 3500);
let distance = space.distance(&other, 1.0);

// Get containing fractal box
let bbox = space.containing_box(2); // Level 2 box

// Subdivide space
let children = bbox.subdivide(); // Creates 27 sub-boxes
```

### 2. Deterministic Noise Functions (`holographic::noise`)

Procedural noise generation for organic patterns.

#### Perlin Noise

```rust
// Basic 3D Perlin noise (-1.0 to 1.0)
let value = perlin_3d(seed, x, y, z);

// Fractal noise with multiple octaves
let fractal = fractal_noise_3d(
    seed,
    x, y, z,
    octaves,     // Number of noise layers
    persistence, // Amplitude decay (0.5 typical)
    lacunarity,  // Frequency increase (2.0 typical)
);
```

#### Advanced Noise Functions

```rust
// Turbulence (absolute value noise)
let turb = turbulence_3d(seed, x, y, z, octaves);

// Ridged noise (mountain-like)
let ridge = ridged_noise_3d(seed, x, y, z, octaves, 0.5);

// Voronoi/Worley noise (cellular patterns)
let (min_dist, second_min) = voronoi_3d(seed, x, y, z);

// Domain warping (organic distortion)
let warped = domain_warp_3d(seed, x, y, z, warp_amount, octaves);
```

### 3. L-System Grammar Engine (`holographic::lsystem`)

Bio-inspired procedural generation using Lindenmayer systems.

#### Basic L-System

```rust
// Create L-System with axiom
let mut lsystem = LSystem::new("A", seed);

// Add production rules
lsystem.add_rule(LSystemRule::simple('A', "AB"));
lsystem.add_rule(LSystemRule::simple('B', "A"));

// Stochastic rules
lsystem.add_rule(LSystemRule::stochastic('X', "XY", 0.7));

// Context-sensitive rules
lsystem.add_rule(LSystemRule::contextual(
    'A', "B",
    Some('X'), // Left context
    Some('Y'), // Right context
));

// Generate string after n iterations
let result = lsystem.generate(5);
```

#### Architectural L-Systems

```rust
// Pre-defined architectural patterns
pub enum ArchitecturePattern {
    Tower,      // Vertical growth
    Branching,  // Tree-like structures
    Grid,       // Rectangular patterns
    Organic,    // Curved growth
    Fractal,    // Self-similar patterns
}

// Generate building structures
let arch = ArchitecturalLSystem::new(
    ArchitecturePattern::Branching,
    building_id,
    seed,
);

// Convert to ArxObjects
let objects = arch.generate_objects(
    iterations,     // Growth iterations
    (x, y, z),     // Base position
);
```

### 4. Cellular Automata System (`holographic::automata`)

3D cellular automata for dynamic system simulation.

#### Automaton Rules

```rust
// Pre-defined rule sets
let rules = AutomatonRules::conway_3d();     // Classic 3D Game of Life
let rules = AutomatonRules::growth_3d();     // Growth patterns
let rules = AutomatonRules::crystal();       // Crystal formation
let rules = AutomatonRules::decay(states, rate); // Multi-state decay

// Custom rules
let rules = AutomatonRules {
    birth: vec![5, 6, 7],      // Neighbor counts for birth
    survival: vec![4, 5, 6],   // Neighbor counts for survival
    states: 2,                 // Number of states
    decay_rate: 0.0,          // Decay rate for multi-state
    neighborhood: NeighborhoodType::Moore, // 26 neighbors
};
```

#### Running Simulations

```rust
// Create automaton with random initial state
let mut ca = CellularAutomaton3D::random(
    width, height, depth,
    rules,
    density, // Initial density (0.0-1.0)
    seed,
);

// Or create empty and add patterns
let mut ca = CellularAutomaton3D::new(10, 10, 10, rules, seed);
ca.set_region(2, 2, 2, 3, 3, 3, 1); // Set a 3x3x3 block
ca.add_glider(5, 5, 5);             // Add glider pattern

// Evolve the system
ca.step();        // Single generation
ca.evolve(100);   // Multiple generations

// Convert to ArxObjects
let objects = ca.to_arxobjects(
    building_id,
    (base_x, base_y, base_z),
    scale, // Size of each cell in mm
);
```

## Complete Example: Procedural Building Generation

```rust
use arxos_core::{
    arxobject::ArxObject,
    holographic::{
        fractal::{FractalSpace, FractalCoordinate},
        noise::{fractal_noise_3d, voronoi_3d},
        lsystem::{ArchitecturalLSystem, ArchitecturePattern},
        automata::{CellularAutomaton3D, AutomatonRules},
    },
};

fn generate_procedural_building(
    building_id: u16,
    seed: u64,
) -> Vec<ArxObject> {
    let mut all_objects = Vec::new();
    
    // Step 1: Generate base structure with L-System
    let arch = ArchitecturalLSystem::new(
        ArchitecturePattern::Tower,
        building_id,
        seed,
    );
    let structure = arch.generate_objects(4, (5000, 5000, 0));
    all_objects.extend(structure);
    
    // Step 2: Add organic details with noise
    for x in 0..10 {
        for y in 0..10 {
            for z in 0..5 {
                let fx = x as f32 * 0.5;
                let fy = y as f32 * 0.5;
                let fz = z as f32 * 0.5;
                
                // Use noise to determine object placement
                let noise = fractal_noise_3d(seed, fx, fy, fz, 3, 0.5, 2.0);
                
                if noise > 0.3 {
                    // Use Voronoi for room divisions
                    let (dist, _) = voronoi_3d(seed ^ 1, fx, fy, fz);
                    
                    let object_type = if dist < 0.5 {
                        object_types::WALL
                    } else {
                        object_types::FLOOR
                    };
                    
                    let obj = ArxObject::new(
                        building_id,
                        object_type,
                        (x * 1000) as u16,
                        (y * 1000) as u16,
                        (z * 3000) as u16,
                    );
                    all_objects.push(obj);
                }
            }
        }
    }
    
    // Step 3: Simulate HVAC system with cellular automata
    let mut hvac_ca = CellularAutomaton3D::random(
        8, 8, 4,
        AutomatonRules::growth_3d(),
        0.2,
        seed ^ 2,
    );
    hvac_ca.evolve(5);
    
    let hvac_objects = hvac_ca.to_arxobjects(
        building_id,
        (2000, 2000, 500),
        500, // 50cm voxels
    );
    
    // Convert CA cells to HVAC components
    for mut obj in hvac_objects {
        obj.object_type = object_types::AIR_VENT;
        all_objects.push(obj);
    }
    
    // Step 4: Use fractal coordinates for infinite detail
    let mut detail_coord = FractalCoordinate::from_mm(5000);
    
    // Zoom in for detailed components
    detail_coord.rescale(3); // Zoom in 3 levels
    
    // Generate sub-components at this scale
    for i in 0..10 {
        let sub_pos = detail_coord.to_absolute(0.1 * i as f32);
        
        let detail_obj = ArxObject::new(
            building_id,
            object_types::OUTLET,
            sub_pos as u16,
            5000,
            1000,
        );
        all_objects.push(detail_obj);
    }
    
    all_objects
}
```

## Performance Considerations

### Memory Usage
- FractalCoordinate: 7 bytes
- Grid3D (10x10x10): ~1KB
- L-System string growth: O(k^n) where k=average rule length, n=iterations

### Computational Complexity
- Perlin noise: O(1) per sample
- Fractal noise: O(octaves) per sample
- L-System generation: O(string_length * rules)
- Cellular automaton step: O(width * height * depth * neighbors)

### Optimization Tips
1. Cache noise values when sampling the same region multiple times
2. Limit L-System iterations (typically 3-6 is sufficient)
3. Use smaller CA grids and scale up the output
4. Pre-generate and store common patterns

## Best Practices

1. **Deterministic Seeds**: Always use deterministic seeds for reproducibility
   ```rust
   let seed = building_id as u64 ^ room_number as u64;
   ```

2. **Scale Management**: Choose appropriate scales for different components
   ```rust
   // Building level: meters
   let building_scale = 1.0;
   
   // Room level: decimeters
   let room_scale = 0.1;
   
   // Component level: centimeters
   let component_scale = 0.01;
   ```

3. **Combine Techniques**: Layer multiple procedural techniques
   ```rust
   // Base structure from L-Systems
   // Details from noise
   // Dynamic systems from CA
   // Infinite zoom with fractals
   ```

4. **Memory Efficiency**: Generate on-demand rather than storing everything
   ```rust
   fn generate_at_position(pos: FractalCoordinate) -> ArxObject {
       // Generate only what's needed at this position/scale
   }
   ```

## Troubleshooting

### Common Issues

1. **Noise returning same values**
   - Ensure different seeds for different noise layers
   - Check coordinate scaling (too small = no variation)

2. **L-System explosion**
   - Limit iteration count
   - Use stochastic rules to control growth

3. **CA patterns dying out**
   - Adjust initial density
   - Try different rule sets
   - Check neighborhood type

4. **Fractal coordinate overflow**
   - Limit zoom depth
   - Use appropriate base scales

## Next Steps

This completes Phase 1 of the Holographic ArxObject implementation. Future phases will add:

- **Phase 2**: Observer Context System (reality manifestation based on observer role)
- **Phase 3**: Quantum Mechanics Simulation (superposition and entanglement)
- **Phase 4**: Consciousness Field System (emergent building consciousness)

See [HOLOGRAPHIC_ARXOBJECT_ENGINEERING_PLAN.md](./HOLOGRAPHIC_ARXOBJECT_ENGINEERING_PLAN.md) for complete implementation details.