//! Core rasterization algorithms for ASCII CAD rendering

use crate::cad::data_model::Point2D;

/// Pixel position on the character grid
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct GridPoint {
    pub x: i32,
    pub y: i32,
}

/// Bresenham's line algorithm for efficient line rasterization
pub fn bresenham_line(start: Point2D, end: Point2D) -> Vec<GridPoint> {
    let mut points = Vec::new();
    
    let x0 = start.x.round() as i32;
    let y0 = start.y.round() as i32;
    let x1 = end.x.round() as i32;
    let y1 = end.y.round() as i32;
    
    let dx = (x1 - x0).abs();
    let dy = (y1 - y0).abs();
    let sx = if x0 < x1 { 1 } else { -1 };
    let sy = if y0 < y1 { 1 } else { -1 };
    let mut err = dx - dy;
    
    let mut x = x0;
    let mut y = y0;
    
    loop {
        points.push(GridPoint { x, y });
        
        if x == x1 && y == y1 {
            break;
        }
        
        let e2 = 2 * err;
        
        if e2 > -dy {
            err -= dy;
            x += sx;
        }
        
        if e2 < dx {
            err += dx;
            y += sy;
        }
    }
    
    points
}

/// Midpoint circle algorithm for efficient circle rasterization
pub fn midpoint_circle(center: Point2D, radius: f64) -> Vec<GridPoint> {
    let mut points = Vec::new();
    
    let cx = center.x.round() as i32;
    let cy = center.y.round() as i32;
    let r = radius.round() as i32;
    
    let mut x = 0;
    let mut y = r;
    let mut d = 1 - r;
    
    // Add initial points in all octants
    add_circle_points(&mut points, cx, cy, x, y);
    
    while x < y {
        x += 1;
        
        if d < 0 {
            d += 2 * x + 1;
        } else {
            y -= 1;
            d += 2 * (x - y) + 1;
        }
        
        add_circle_points(&mut points, cx, cy, x, y);
    }
    
    points
}

/// Helper to add symmetric circle points
fn add_circle_points(points: &mut Vec<GridPoint>, cx: i32, cy: i32, x: i32, y: i32) {
    points.push(GridPoint { x: cx + x, y: cy + y });
    points.push(GridPoint { x: cx - x, y: cy + y });
    points.push(GridPoint { x: cx + x, y: cy - y });
    points.push(GridPoint { x: cx - x, y: cy - y });
    points.push(GridPoint { x: cx + y, y: cy + x });
    points.push(GridPoint { x: cx - y, y: cy + x });
    points.push(GridPoint { x: cx + y, y: cy - x });
    points.push(GridPoint { x: cx - y, y: cy - x });
}

/// Draw an arc using parametric equations
pub fn draw_arc(center: Point2D, radius: f64, start_angle: f64, end_angle: f64) -> Vec<GridPoint> {
    let mut points = Vec::new();
    
    // Normalize angles to 0..2π
    let start = start_angle.rem_euclid(2.0 * std::f64::consts::PI);
    let mut end = end_angle.rem_euclid(2.0 * std::f64::consts::PI);
    
    if end <= start {
        end += 2.0 * std::f64::consts::PI;
    }
    
    // Sample points along the arc
    let steps = (radius * (end - start)).round() as usize;
    let step_size = (end - start) / steps as f64;
    
    for i in 0..=steps {
        let angle = start + (i as f64 * step_size);
        let x = center.x + radius * angle.cos();
        let y = center.y + radius * angle.sin();
        
        let grid_point = GridPoint {
            x: x.round() as i32,
            y: y.round() as i32,
        };
        
        // Avoid duplicates
        if points.last() != Some(&grid_point) {
            points.push(grid_point);
        }
    }
    
    points
}

/// Draw a rectangle
pub fn draw_rectangle(origin: Point2D, width: f64, height: f64) -> Vec<GridPoint> {
    let mut points = Vec::new();
    
    let top_left = origin;
    let top_right = Point2D { x: origin.x + width, y: origin.y };
    let bottom_right = Point2D { x: origin.x + width, y: origin.y + height };
    let bottom_left = Point2D { x: origin.x, y: origin.y + height };
    
    // Draw four sides
    points.extend(bresenham_line(top_left, top_right));
    points.extend(bresenham_line(top_right, bottom_right));
    points.extend(bresenham_line(bottom_right, bottom_left));
    points.extend(bresenham_line(bottom_left, top_left));
    
    points
}

/// Draw a polyline (connected line segments)
pub fn draw_polyline(points: &[Point2D], is_closed: bool) -> Vec<GridPoint> {
    let mut grid_points = Vec::new();
    
    if points.len() < 2 {
        return grid_points;
    }
    
    // Draw lines between consecutive points
    for window in points.windows(2) {
        grid_points.extend(bresenham_line(window[0], window[1]));
    }
    
    // Close the polyline if requested
    if is_closed && points.len() > 2 {
        grid_points.extend(bresenham_line(
            points[points.len() - 1],
            points[0]
        ));
    }
    
    grid_points
}

/// Wu's antialiasing line algorithm (returns points with intensity)
pub struct AntialiasedPoint {
    pub x: i32,
    pub y: i32,
    pub intensity: f64,  // 0.0 to 1.0
}

pub fn wu_line(start: Point2D, end: Point2D) -> Vec<AntialiasedPoint> {
    let mut points = Vec::new();
    
    let mut x0 = start.x;
    let mut y0 = start.y;
    let mut x1 = end.x;
    let mut y1 = end.y;
    
    let steep = (y1 - y0).abs() > (x1 - x0).abs();
    
    if steep {
        std::mem::swap(&mut x0, &mut y0);
        std::mem::swap(&mut x1, &mut y1);
    }
    
    if x0 > x1 {
        std::mem::swap(&mut x0, &mut x1);
        std::mem::swap(&mut y0, &mut y1);
    }
    
    let dx = x1 - x0;
    let dy = y1 - y0;
    let gradient = if dx == 0.0 { 1.0 } else { dy / dx };
    
    // Handle first endpoint
    let xend = x0.round();
    let yend = y0 + gradient * (xend - x0);
    let xgap = 1.0 - (x0 + 0.5).fract();
    let xpxl1 = xend as i32;
    let ypxl1 = yend.floor() as i32;
    
    if steep {
        points.push(AntialiasedPoint {
            x: ypxl1,
            y: xpxl1,
            intensity: (1.0 - yend.fract()) * xgap,
        });
        points.push(AntialiasedPoint {
            x: ypxl1 + 1,
            y: xpxl1,
            intensity: yend.fract() * xgap,
        });
    } else {
        points.push(AntialiasedPoint {
            x: xpxl1,
            y: ypxl1,
            intensity: (1.0 - yend.fract()) * xgap,
        });
        points.push(AntialiasedPoint {
            x: xpxl1,
            y: ypxl1 + 1,
            intensity: yend.fract() * xgap,
        });
    }
    
    let mut intery = yend + gradient;
    
    // Handle second endpoint
    let xend = x1.round();
    let yend = y1 + gradient * (xend - x1);
    let xgap = (x1 + 0.5).fract();
    let xpxl2 = xend as i32;
    let ypxl2 = yend.floor() as i32;
    
    if steep {
        points.push(AntialiasedPoint {
            x: ypxl2,
            y: xpxl2,
            intensity: (1.0 - yend.fract()) * xgap,
        });
        points.push(AntialiasedPoint {
            x: ypxl2 + 1,
            y: xpxl2,
            intensity: yend.fract() * xgap,
        });
    } else {
        points.push(AntialiasedPoint {
            x: xpxl2,
            y: ypxl2,
            intensity: (1.0 - yend.fract()) * xgap,
        });
        points.push(AntialiasedPoint {
            x: xpxl2,
            y: ypxl2 + 1,
            intensity: yend.fract() * xgap,
        });
    }
    
    // Main loop
    for x in (xpxl1 + 1)..xpxl2 {
        if steep {
            points.push(AntialiasedPoint {
                x: intery.floor() as i32,
                y: x,
                intensity: 1.0 - intery.fract(),
            });
            points.push(AntialiasedPoint {
                x: intery.floor() as i32 + 1,
                y: x,
                intensity: intery.fract(),
            });
        } else {
            points.push(AntialiasedPoint {
                x,
                y: intery.floor() as i32,
                intensity: 1.0 - intery.fract(),
            });
            points.push(AntialiasedPoint {
                x,
                y: intery.floor() as i32 + 1,
                intensity: intery.fract(),
            });
        }
        intery += gradient;
    }
    
    points
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_bresenham_line() {
        let start = Point2D { x: 0.0, y: 0.0 };
        let end = Point2D { x: 5.0, y: 5.0 };
        let points = bresenham_line(start, end);
        
        assert_eq!(points.len(), 6);
        assert_eq!(points[0], GridPoint { x: 0, y: 0 });
        assert_eq!(points[5], GridPoint { x: 5, y: 5 });
    }
    
    #[test]
    fn test_midpoint_circle() {
        let center = Point2D { x: 10.0, y: 10.0 };
        let points = midpoint_circle(center, 5.0);
        
        // Circle should have points at cardinal directions
        assert!(points.contains(&GridPoint { x: 15, y: 10 }));  // Right
        assert!(points.contains(&GridPoint { x: 5, y: 10 }));   // Left
        assert!(points.contains(&GridPoint { x: 10, y: 15 }));  // Bottom
        assert!(points.contains(&GridPoint { x: 10, y: 5 }));   // Top
    }
}