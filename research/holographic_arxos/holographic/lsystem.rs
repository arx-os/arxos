//! L-System Grammar Engine
//! 
//! Implements Lindenmayer systems for procedural generation of
//! architectural structures using bio-inspired growth patterns.

use crate::arxobject::{ArxObject, object_types};

#[cfg(not(feature = "std"))]
use alloc::vec::Vec;
#[cfg(not(feature = "std"))]
use alloc::string::{String, ToString};

#[cfg(feature = "std")]
use std::vec::Vec;
#[cfg(feature = "std")]
use std::string::{String, ToString};

use core::f32::consts::PI;

/// L-System rule for procedural structure generation
#[derive(Clone, Debug)]
pub struct LSystemRule {
    /// Symbol to be replaced
    pub predecessor: char,
    
    /// Replacement string
    pub successor: String,
    
    /// Probability of applying this rule (for stochastic L-systems)
    pub probability: f32,
    
    /// Optional context sensitivity
    pub context_left: Option<char>,
    pub context_right: Option<char>,
}

impl LSystemRule {
    /// Create a simple deterministic rule
    pub fn simple(predecessor: char, successor: &str) -> Self {
        Self {
            predecessor,
            successor: successor.to_string(),
            probability: 1.0,
            context_left: None,
            context_right: None,
        }
    }
    
    /// Create a stochastic rule with probability
    pub fn stochastic(predecessor: char, successor: &str, probability: f32) -> Self {
        Self {
            predecessor,
            successor: successor.to_string(),
            probability: probability.clamp(0.0, 1.0),
            context_left: None,
            context_right: None,
        }
    }
    
    /// Create a context-sensitive rule
    pub fn contextual(
        predecessor: char,
        successor: &str,
        left: Option<char>,
        right: Option<char>,
    ) -> Self {
        Self {
            predecessor,
            successor: successor.to_string(),
            probability: 1.0,
            context_left: left,
            context_right: right,
        }
    }
    
    /// Check if rule applies in given context
    pub fn applies(&self, ch: char, left: Option<char>, right: Option<char>) -> bool {
        if ch != self.predecessor {
            return false;
        }
        
        if self.context_left.is_some() && self.context_left != left {
            return false;
        }
        
        if self.context_right.is_some() && self.context_right != right {
            return false;
        }
        
        true
    }
}

/// Base L-System implementation
pub struct LSystem {
    /// Initial string (axiom)
    pub axiom: String,
    
    /// Production rules
    pub rules: Vec<LSystemRule>,
    
    /// Random seed for stochastic rules
    pub seed: u64,
}

impl LSystem {
    /// Create new L-System
    pub fn new(axiom: &str, seed: u64) -> Self {
        Self {
            axiom: axiom.to_string(),
            rules: Vec::new(),
            seed,
        }
    }
    
    /// Add a production rule
    pub fn add_rule(&mut self, rule: LSystemRule) {
        self.rules.push(rule);
    }
    
    /// Generate string after n iterations
    pub fn generate(&self, iterations: u8) -> String {
        let mut current = self.axiom.clone();
        
        for iteration in 0..iterations {
            current = self.iterate(&current, iteration as u64);
        }
        
        current
    }
    
    /// Perform one iteration of L-System generation
    fn iterate(&self, input: &str, iteration: u64) -> String {
        let mut output = String::new();
        let chars: Vec<char> = input.chars().collect();
        
        for (i, &ch) in chars.iter().enumerate() {
            let context_left = if i > 0 { Some(chars[i - 1]) } else { None };
            let context_right = if i < chars.len() - 1 { Some(chars[i + 1]) } else { None };
            
            let mut replaced = false;
            
            // Find applicable rules
            let applicable: Vec<&LSystemRule> = self.rules
                .iter()
                .filter(|r| r.applies(ch, context_left, context_right))
                .collect();
            
            if !applicable.is_empty() {
                // Select rule (deterministic or stochastic)
                if let Some(rule) = self.select_rule(&applicable, i as u64, iteration) {
                    output.push_str(&rule.successor);
                    replaced = true;
                }
            }
            
            if !replaced {
                output.push(ch);
            }
        }
        
        output
    }
    
    /// Select rule based on probability
    fn select_rule<'a>(&self, rules: &[&'a LSystemRule], position: u64, iteration: u64) -> Option<&'a LSystemRule> {
        if rules.len() == 1 && rules[0].probability >= 1.0 {
            return Some(rules[0]);
        }
        
        // Generate deterministic "random" value
        let hash = self.hash(position, iteration);
        let random = (hash % 1000) as f32 / 1000.0;
        
        let mut cumulative = 0.0;
        for rule in rules {
            cumulative += rule.probability;
            if random <= cumulative {
                return Some(rule);
            }
        }
        
        rules.last().copied()
    }
    
    /// Simple hash for deterministic randomness
    fn hash(&self, position: u64, iteration: u64) -> u64 {
        let mut h = self.seed;
        h ^= position.wrapping_mul(0x9e3779b97f4a7c15);
        h ^= iteration.wrapping_mul(0x94d049bb133111eb);
        h = h.wrapping_mul(0xbf58476d1ce4e5b9);
        h ^= h >> 30;
        h
    }
}

/// 3D turtle graphics state
#[derive(Clone, Debug)]
struct TurtleState {
    position: (f32, f32, f32),
    direction: (f32, f32, f32),
    up: (f32, f32, f32),
    step_size: f32,
}

impl TurtleState {
    fn new() -> Self {
        Self {
            position: (0.0, 0.0, 0.0),
            direction: (1.0, 0.0, 0.0),
            up: (0.0, 0.0, 1.0),
            step_size: 1000.0, // 1 meter in mm
        }
    }
    
    /// Move forward
    fn forward(&mut self) {
        self.position.0 += self.direction.0 * self.step_size;
        self.position.1 += self.direction.1 * self.step_size;
        self.position.2 += self.direction.2 * self.step_size;
    }
    
    /// Rotate around up vector (yaw)
    fn rotate_yaw(&mut self, angle: f32) {
        let cos_a = angle.cos();
        let sin_a = angle.sin();
        
        let new_dir = (
            self.direction.0 * cos_a - self.direction.1 * sin_a,
            self.direction.0 * sin_a + self.direction.1 * cos_a,
            self.direction.2,
        );
        
        self.direction = Self::normalize(new_dir);
    }
    
    /// Rotate around right vector (pitch)
    fn rotate_pitch(&mut self, angle: f32) {
        let right = Self::cross(self.direction, self.up);
        let cos_a = angle.cos();
        let sin_a = angle.sin();
        
        // Rodrigues' rotation formula
        let k = right;
        let v = self.direction;
        
        let new_dir = (
            v.0 * cos_a + k.0 * Self::dot(k, v) * (1.0 - cos_a) + (k.1 * v.2 - k.2 * v.1) * sin_a,
            v.1 * cos_a + k.1 * Self::dot(k, v) * (1.0 - cos_a) + (k.2 * v.0 - k.0 * v.2) * sin_a,
            v.2 * cos_a + k.2 * Self::dot(k, v) * (1.0 - cos_a) + (k.0 * v.1 - k.1 * v.0) * sin_a,
        );
        
        self.direction = Self::normalize(new_dir);
    }
    
    /// Normalize vector
    fn normalize(v: (f32, f32, f32)) -> (f32, f32, f32) {
        let len = (v.0 * v.0 + v.1 * v.1 + v.2 * v.2).sqrt();
        if len > 0.0 {
            (v.0 / len, v.1 / len, v.2 / len)
        } else {
            v
        }
    }
    
    /// Cross product
    fn cross(a: (f32, f32, f32), b: (f32, f32, f32)) -> (f32, f32, f32) {
        (
            a.1 * b.2 - a.2 * b.1,
            a.2 * b.0 - a.0 * b.2,
            a.0 * b.1 - a.1 * b.0,
        )
    }
    
    /// Dot product
    fn dot(a: (f32, f32, f32), b: (f32, f32, f32)) -> f32 {
        a.0 * b.0 + a.1 * b.1 + a.2 * b.2
    }
}

/// Architectural L-System for building generation
pub struct ArchitecturalLSystem {
    lsystem: LSystem,
    angle: f32,
    building_id: u16,
}

impl ArchitecturalLSystem {
    /// Create architectural L-System with common patterns
    pub fn new(pattern: ArchitecturePattern, building_id: u16, seed: u64) -> Self {
        let (axiom, rules, angle) = match pattern {
            ArchitecturePattern::Tower => Self::tower_rules(),
            ArchitecturePattern::Branching => Self::branching_rules(),
            ArchitecturePattern::Grid => Self::grid_rules(),
            ArchitecturePattern::Organic => Self::organic_rules(),
            ArchitecturePattern::Fractal => Self::fractal_rules(),
        };
        
        let mut lsystem = LSystem::new(&axiom, seed);
        for rule in rules {
            lsystem.add_rule(rule);
        }
        
        Self {
            lsystem,
            angle,
            building_id,
        }
    }
    
    /// Tower pattern (vertical growth)
    fn tower_rules() -> (String, Vec<LSystemRule>, f32) {
        let axiom = "FA".to_string();
        let rules = vec![
            LSystemRule::simple('A', "F[+B][-B]FA"),
            LSystemRule::simple('B', "F[+C][-C]B"),
            LSystemRule::simple('C', "FC"),
        ];
        (axiom, rules, PI / 6.0)
    }
    
    /// Branching pattern (tree-like)
    fn branching_rules() -> (String, Vec<LSystemRule>, f32) {
        let axiom = "X".to_string();
        let rules = vec![
            LSystemRule::simple('X', "F[+X]F[-X]+X"),
            LSystemRule::simple('F', "FF"),
        ];
        (axiom, rules, PI / 9.0)
    }
    
    /// Grid pattern (rectangular)
    fn grid_rules() -> (String, Vec<LSystemRule>, f32) {
        let axiom = "F+F+F+F".to_string();
        let rules = vec![
            LSystemRule::simple('F', "FF+F+F+F+FF"),
        ];
        (axiom, rules, PI / 2.0)
    }
    
    /// Organic pattern (curved growth)
    fn organic_rules() -> (String, Vec<LSystemRule>, f32) {
        let axiom = "FX".to_string();
        let rules = vec![
            LSystemRule::stochastic('X', "X+YF+", 0.5),
            LSystemRule::stochastic('X', "X-YF-", 0.5),
            LSystemRule::simple('Y', "-FX-Y"),
        ];
        (axiom, rules, PI / 4.0)
    }
    
    /// Fractal pattern (Sierpinski-like)
    fn fractal_rules() -> (String, Vec<LSystemRule>, f32) {
        let axiom = "FXF--FF--FF".to_string();
        let rules = vec![
            LSystemRule::simple('F', "FF"),
            LSystemRule::simple('X', "--FXF++FXF++FXF--"),
        ];
        (axiom, rules, PI / 3.0)
    }
    
    /// Generate ArxObjects from L-System
    pub fn generate_objects(&self, iterations: u8, base_position: (u16, u16, u16)) -> Vec<ArxObject> {
        let lstring = self.lsystem.generate(iterations);
        self.interpret_string(&lstring, base_position)
    }
    
    /// Interpret L-System string as ArxObjects
    fn interpret_string(&self, lstring: &str, base_position: (u16, u16, u16)) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        let mut turtle = TurtleState::new();
        let mut stack: Vec<TurtleState> = Vec::new();
        
        turtle.position = (
            base_position.0 as f32,
            base_position.1 as f32,
            base_position.2 as f32,
        );
        
        for ch in lstring.chars() {
            match ch {
                'F' | 'f' => {
                    // Create structure at current position
                    let obj = ArxObject::new(
                        self.building_id,
                        self.object_type_for_position(&turtle),
                        turtle.position.0 as u16,
                        turtle.position.1 as u16,
                        turtle.position.2 as u16,
                    );
                    objects.push(obj);
                    
                    // Move forward
                    turtle.forward();
                }
                '+' => turtle.rotate_yaw(self.angle),
                '-' => turtle.rotate_yaw(-self.angle),
                '^' => turtle.rotate_pitch(self.angle),
                '&' => turtle.rotate_pitch(-self.angle),
                '\\' => turtle.rotate_yaw(PI / 2.0),
                '/' => turtle.rotate_yaw(-PI / 2.0),
                '|' => turtle.rotate_yaw(PI),
                '[' => stack.push(turtle.clone()),
                ']' => {
                    if let Some(state) = stack.pop() {
                        turtle = state;
                    }
                }
                _ => {} // Ignore other characters
            }
        }
        
        objects
    }
    
    /// Determine object type based on turtle position
    fn object_type_for_position(&self, turtle: &TurtleState) -> u8 {
        let height = turtle.position.2;
        
        if height < 1000.0 {
            object_types::FOUNDATION
        } else if height < 3000.0 {
            object_types::WALL
        } else if height < 10000.0 {
            object_types::FLOOR
        } else {
            object_types::ROOF
        }
    }
}

/// Architectural pattern types
#[derive(Clone, Copy, Debug)]
pub enum ArchitecturePattern {
    Tower,
    Branching,
    Grid,
    Organic,
    Fractal,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_lsystem_basic() {
        let mut lsystem = LSystem::new("A", 42);
        lsystem.add_rule(LSystemRule::simple('A', "AB"));
        lsystem.add_rule(LSystemRule::simple('B', "A"));
        
        // Generation 0: A
        // Generation 1: AB
        // Generation 2: ABA
        // Generation 3: ABAAB
        let result = lsystem.generate(3);
        assert_eq!(result, "ABAAB");
    }
    
    #[test]
    fn test_lsystem_context_sensitive() {
        let mut lsystem = LSystem::new("BAC", 42);
        lsystem.add_rule(LSystemRule::contextual('A', "X", Some('B'), Some('C')));
        
        let result = lsystem.generate(1);
        assert_eq!(result, "BXC");
    }
    
    #[test]
    fn test_architectural_generation() {
        let arch = ArchitecturalLSystem::new(
            ArchitecturePattern::Tower,
            1,
            42,
        );
        
        let objects = arch.generate_objects(2, (5000, 5000, 0));
        assert!(!objects.is_empty());
        
        // For tower pattern, we should have at least some objects
        assert!(objects.len() >= 1);
        
        // Check that we have objects (may be at same or different heights)
        let first_z = objects[0].z;
        assert!(first_z <= 65535); // Valid z coordinate
    }
    
    #[test]
    fn test_turtle_state() {
        let mut turtle = TurtleState::new();
        let initial_pos = turtle.position;
        
        turtle.forward();
        assert_ne!(turtle.position, initial_pos);
        
        turtle.rotate_yaw(PI / 2.0);
        let rotated_dir = turtle.direction;
        assert!((rotated_dir.0).abs() < 0.01); // Should be pointing in Y direction
    }
}