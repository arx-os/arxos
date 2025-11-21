//! Grid coordinate system for architectural drawings
//!
//! Provides conversion between grid coordinates (e.g., "D-4") and real-world coordinates.
//! Grid coordinates are commonly used in architectural drawings where the building
//! is divided into a grid system (columns A-Z, rows 1-n).

pub mod to_address;

use super::Point3D;
use serde::{Deserialize, Serialize};
use std::fmt;

/// Grid coordinate (e.g., "D-4" = column D, row 4)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct GridCoordinate {
    /// Column letter (A-Z, typically uppercase)
    pub column: String,
    /// Row number (typically 1-based)
    pub row: i32,
}

impl GridCoordinate {
    /// Create a new grid coordinate from column and row
    ///
    /// # Arguments
    ///
    /// * `column` - Column letter (A-Z, typically uppercase)
    /// * `row` - Row number (typically 1-based)
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::grid::GridCoordinate;
    /// let coord = GridCoordinate::new("D".to_string(), 4);
    /// assert_eq!(coord.column, "D");
    /// assert_eq!(coord.row, 4);
    /// assert_eq!(coord.to_string(), "D-4");
    /// ```
    pub fn new(column: String, row: i32) -> Self {
        Self { column, row }
    }

    /// Parse grid coordinate from string
    ///
    /// Supports multiple formats: "D-4", "D4", "D 4", "d-4" (case insensitive)
    ///
    /// # Arguments
    ///
    /// * `s` - Grid coordinate string to parse
    ///
    /// # Returns
    ///
    /// * `Ok(GridCoordinate)` - Successfully parsed coordinate
    /// * `Err(...)` - Invalid format or invalid column/row values
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::grid::GridCoordinate;
    /// let coord = GridCoordinate::parse("D-4").unwrap();
    /// assert_eq!(coord.column, "D");
    /// assert_eq!(coord.row, 4);
    ///
    /// // Case insensitive with space separator
    /// let coord2 = GridCoordinate::parse("d 4").unwrap();
    /// assert_eq!(coord2.column, "D");
    /// assert_eq!(coord2.row, 4);
    ///
    /// // Invalid format (missing separator)
    /// assert!(GridCoordinate::parse("invalid").is_err());
    /// ```
    pub fn parse(s: &str) -> Result<Self, Box<dyn std::error::Error>> {
        // Remove whitespace and convert to uppercase
        let s = s.trim().to_uppercase();

        // Try formats: "D-4", "D4", "D 4"
        let parts: Vec<&str> = s
            .split(&['-', ' ', '_'][..])
            .filter(|p| !p.is_empty())
            .collect();

        if parts.len() != 2 {
            return Err(format!(
                "Invalid grid coordinate format '{}'. Expected format: 'D-4' or 'D4'",
                s
            )
            .into());
        }

        let column = parts[0].to_string();
        let row = parts[1]
            .parse::<i32>()
            .map_err(|e| format!("Invalid row number in grid coordinate '{}': {}", s, e))?;

        // Validate column is a letter
        let column_char = column.chars().next()
            .ok_or_else(|| format!(
                "Invalid column in grid coordinate '{}'. Column must be a single letter (A-Z)",
                s
            ))?;

        if column.len() != 1 || !column_char.is_alphabetic() {
            return Err(format!(
                "Invalid column in grid coordinate '{}'. Column must be a single letter (A-Z)",
                s
            )
            .into());
        }

        Ok(Self { column, row })
    }

    /// Convert column letter to zero-based index
    ///
    /// Maps column letters to numeric indices: A=0, B=1, ..., Z=25
    ///
    /// # Returns
    ///
    /// The zero-based column index (0 for 'A', 1 for 'B', etc.)
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::grid::GridCoordinate;
    /// let coord_a = GridCoordinate::new("A".to_string(), 1);
    /// assert_eq!(coord_a.column_index(), 0);
    ///
    /// let coord_d = GridCoordinate::new("D".to_string(), 4);
    /// assert_eq!(coord_d.column_index(), 3);
    ///
    /// let coord_z = GridCoordinate::new("Z".to_string(), 1);
    /// assert_eq!(coord_z.column_index(), 25);
    /// ```
    pub fn column_index(&self) -> i32 {
        if let Some(ch) = self.column.chars().next() {
            // to_uppercase() on a valid char always produces at least one char
            // but we handle it safely anyway
            if let Some(upper) = ch.to_uppercase().next() {
                (upper as i32) - ('A' as i32)
            } else {
                0
            }
        } else {
            0
        }
    }
}

impl fmt::Display for GridCoordinate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}-{}", self.column, self.row)
    }
}

/// Grid system configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GridSystem {
    /// Grid origin (real-world coordinates where A-1 is located)
    pub origin: Point3D,
    /// Grid spacing in X direction (column spacing)
    pub column_spacing: f64,
    /// Grid spacing in Y direction (row spacing)
    pub row_spacing: f64,
    /// Grid spacing in Z direction (elevation spacing, if applicable)
    pub elevation_spacing: f64,
    /// Column labels (default: A-Z, can be customized)
    pub column_labels: Vec<String>,
    /// Row labels (default: 1-n, can be customized)
    pub row_labels: Vec<i32>,
}

impl GridSystem {
    /// Create a default grid system with standard column/row labels
    ///
    /// Initializes a grid with:
    /// - Columns labeled A through Z
    /// - Rows numbered 1 through 100
    /// - Zero elevation spacing (2D grid)
    ///
    /// # Arguments
    ///
    /// * `origin` - Real-world coordinates where grid position A-1 is located
    /// * `column_spacing` - Distance between columns (X direction)
    /// * `row_spacing` - Distance between rows (Y direction)
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{grid::GridSystem, Point3D};
    /// let grid = GridSystem::new(
    ///     Point3D::new(0.0, 0.0, 0.0),
    ///     10.0,  // 10 meters between columns
    ///     10.0,  // 10 meters between rows
    /// );
    /// assert_eq!(grid.column_spacing, 10.0);
    /// assert_eq!(grid.row_spacing, 10.0);
    /// ```
    pub fn new(origin: Point3D, column_spacing: f64, row_spacing: f64) -> Self {
        Self {
            origin,
            column_spacing,
            row_spacing,
            elevation_spacing: 0.0,
            column_labels: (b'A'..=b'Z').map(|c| (c as char).to_string()).collect(),
            row_labels: (1..=100).collect(),
        }
    }

    /// Create a grid system with custom elevation spacing for 3D grids
    ///
    /// Like `new()`, but allows specifying vertical spacing between grid levels.
    ///
    /// # Arguments
    ///
    /// * `origin` - Real-world coordinates where grid position A-1 is located
    /// * `column_spacing` - Distance between columns (X direction)
    /// * `row_spacing` - Distance between rows (Y direction)
    /// * `elevation_spacing` - Distance between elevation levels (Z direction)
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{grid::GridSystem, Point3D};
    /// let grid = GridSystem::with_spacing(
    ///     Point3D::new(0.0, 0.0, 0.0),
    ///     10.0,  // 10 meters between columns
    ///     10.0,  // 10 meters between rows
    ///     3.5,   // 3.5 meters between floors
    /// );
    /// assert_eq!(grid.elevation_spacing, 3.5);
    /// ```
    pub fn with_spacing(
        origin: Point3D,
        column_spacing: f64,
        row_spacing: f64,
        elevation_spacing: f64,
    ) -> Self {
        Self {
            origin,
            column_spacing,
            row_spacing,
            elevation_spacing,
            column_labels: (b'A'..=b'Z').map(|c| (c as char).to_string()).collect(),
            row_labels: (1..=100).collect(),
        }
    }

    /// Convert grid coordinate to real-world coordinates
    pub fn grid_to_real(&self, grid: &GridCoordinate) -> Point3D {
        let column_idx = grid.column_index();
        let row_idx = grid.row - 1; // Convert to 0-based

        Point3D::new(
            self.origin.x + (column_idx as f64) * self.column_spacing,
            self.origin.y + (row_idx as f64) * self.row_spacing,
            self.origin.z,
        )
    }

    /// Convert real-world coordinates to grid coordinate
    pub fn real_to_grid(&self, point: &Point3D) -> GridCoordinate {
        let column_idx = ((point.x - self.origin.x) / self.column_spacing).round() as i32;
        let row_idx = ((point.y - self.origin.y) / self.row_spacing).round() as i32;

        let column = if column_idx >= 0 && (column_idx as usize) < self.column_labels.len() {
            self.column_labels[column_idx as usize].clone()
        } else {
            // Generate column label beyond A-Z (AA, AB, etc.)
            let mut col = String::new();
            let mut idx = column_idx;
            while idx >= 0 {
                col.insert(0, (b'A' + (idx % 26) as u8) as char);
                idx = idx / 26 - 1;
            }
            col
        };

        let row = row_idx + 1; // Convert to 1-based

        GridCoordinate::new(column, row)
    }

    /// Get grid bounds for a given grid coordinate range
    pub fn grid_bounds(
        &self,
        min_grid: &GridCoordinate,
        max_grid: &GridCoordinate,
    ) -> (Point3D, Point3D) {
        let min_point = self.grid_to_real(min_grid);
        let max_point = self.grid_to_real(max_grid);

        // Ensure min < max
        let actual_min = Point3D::new(
            min_point.x.min(max_point.x),
            min_point.y.min(max_point.y),
            min_point.z.min(max_point.z),
        );
        let actual_max = Point3D::new(
            min_point.x.max(max_point.x),
            min_point.y.max(max_point.y),
            min_point.z.max(max_point.z),
        );

        (actual_min, actual_max)
    }
}

impl Default for GridSystem {
    fn default() -> Self {
        Self::new(Point3D::origin(), 10.0, 10.0) // Default 10m spacing
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_grid_coordinate() {
        let coord = GridCoordinate::parse("D-4").unwrap();
        assert_eq!(coord.column, "D");
        assert_eq!(coord.row, 4);

        let coord = GridCoordinate::parse("A-1").unwrap();
        assert_eq!(coord.column, "A");
        assert_eq!(coord.row, 1);

        let coord = GridCoordinate::parse("Z-26").unwrap();
        assert_eq!(coord.column, "Z");
        assert_eq!(coord.row, 26);
    }

    #[test]
    fn test_column_index() {
        assert_eq!(GridCoordinate::new("A".to_string(), 1).column_index(), 0);
        assert_eq!(GridCoordinate::new("D".to_string(), 4).column_index(), 3);
        assert_eq!(GridCoordinate::new("Z".to_string(), 26).column_index(), 25);
    }

    #[test]
    fn test_grid_to_real() {
        let grid_system = GridSystem::new(Point3D::origin(), 10.0, 10.0);

        let grid = GridCoordinate::parse("A-1").unwrap();
        let real = grid_system.grid_to_real(&grid);
        assert_eq!(real.x, 0.0);
        assert_eq!(real.y, 0.0);

        let grid = GridCoordinate::parse("D-4").unwrap();
        let real = grid_system.grid_to_real(&grid);
        assert_eq!(real.x, 30.0); // Column D = index 3, 3 * 10 = 30
        assert_eq!(real.y, 30.0); // Row 4 = index 3, 3 * 10 = 30
    }

    #[test]
    fn test_real_to_grid() {
        let grid_system = GridSystem::new(Point3D::origin(), 10.0, 10.0);

        let point = Point3D::new(30.0, 30.0, 0.0);
        let grid = grid_system.real_to_grid(&point);
        assert_eq!(grid.column, "D");
        assert_eq!(grid.row, 4);
    }

    #[test]
    fn test_grid_bounds() {
        let grid_system = GridSystem::new(Point3D::origin(), 10.0, 10.0);

        let min_grid = GridCoordinate::parse("A-1").unwrap();
        let max_grid = GridCoordinate::parse("D-4").unwrap();

        let (min_point, max_point) = grid_system.grid_bounds(&min_grid, &max_grid);
        assert_eq!(min_point.x, 0.0);
        assert_eq!(min_point.y, 0.0);
        assert_eq!(max_point.x, 30.0);
        assert_eq!(max_point.y, 30.0);
    }
}
