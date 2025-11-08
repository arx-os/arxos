// Terminal rendering for ArxOS
use arx::core::{Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType, Floor, Room};
use arx::yaml::BuildingData;

pub struct BuildingRenderer {
    building_data: BuildingData,
}

impl BuildingRenderer {
    pub fn new(building_data: BuildingData) -> Self {
        Self { building_data }
    }

    pub fn floors(&self) -> &Vec<Floor> {
        &self.building_data.floors
    }

    pub fn render_floor(&self, floor: i32) -> Result<(), Box<dyn std::error::Error>> {
        // Find the floor data
        let floor_data = self
            .building_data
            .floors
            .iter()
            .find(|f| f.level == floor)
            .ok_or_else(|| format!("Floor {} not found in building data", floor))?;

        println!(
            "Building {} - Floor {} ({})",
            self.building_data.building.name, floor, floor_data.name
        );

        // Render the floor plan
        self.render_floor_plan(floor_data)?;

        // Render equipment status summary
        self.render_equipment_summary(floor_data)?;

        Ok(())
    }

    fn render_floor_plan(&self, floor: &Floor) -> Result<(), Box<dyn std::error::Error>> {
        // Collect all rooms from wings
        let all_rooms: Vec<&Room> = floor
            .wings
            .iter()
            .flat_map(|wing| wing.rooms.iter())
            .collect();

        if all_rooms.is_empty() && floor.equipment.is_empty() {
            println!("┌─────────────────────────────────────────────────────────────┐");
            println!("│                    No data available                        │");
            println!("└─────────────────────────────────────────────────────────────┘");
            return Ok(());
        }

        // Calculate floor bounds (using X-Y plane for top-down view - polygon data uses X-Y)
        let bounds = self.calculate_floor_bounds(floor);
        let (min_x, min_y, max_x, max_y) = bounds;

        // Calculate actual dimensions
        let actual_width = max_x - min_x;
        let actual_height = max_y - min_y;

        if actual_width <= 0.0 || actual_height <= 0.0 {
            // Fallback to minimal size
            let width = 61;
            let height = 30;
            let grid = vec![vec![' '; width]; height];
            println!("┌─────────────────────────────────────────────────────────────┐");
            for row in grid {
                println!("│ {:<61} │", row.iter().collect::<String>());
            }
            println!("└─────────────────────────────────────────────────────────────┘");
            return Ok(());
        }

        // Preserve aspect ratio - scale to fit terminal while maintaining shape
        let max_terminal_width = 61;
        let max_terminal_height = 30;

        // Calculate scale to fit in terminal (preserve aspect ratio)
        let polygon_aspect = actual_width / actual_height;
        let terminal_aspect = max_terminal_width as f64 / max_terminal_height as f64;

        let (width, height) = if polygon_aspect > terminal_aspect {
            // Polygon is wider - constrained by width
            let width = max_terminal_width;
            let height = ((max_terminal_width as f64 / polygon_aspect) as usize).max(1);
            (width, height)
        } else {
            // Polygon is taller - constrained by height
            let height = max_terminal_height;
            let width = ((max_terminal_height as f64 * polygon_aspect) as usize).max(1);
            (width, height)
        };

        // Create ASCII grid
        let mut grid = vec![vec![' '; width]; height];

        // Draw rooms (polygon outline IS the wall structure)
        for room in &all_rooms {
            self.draw_room(&mut grid[..], room, bounds, 1.0)?;
        }

        // Draw interior walls ONLY if they're in polygon coordinate space
        // (Skip world-space walls that don't align with polygon)
        for room in &all_rooms {
            if let Some(walls_str) = room.properties.get("walls_data") {
                if !walls_str.is_empty() {
                    // Only draw walls that are clearly in the polygon's coordinate space
                    // (within reasonable bounds of the polygon)
                    self.draw_walls_in_polygon_space(&mut grid, walls_str, bounds, width, height)?;
                }
            }
        }

        // Draw equipment
        for equipment in &floor.equipment {
            self.draw_equipment(&mut grid, equipment, bounds, 1.0)?;
        }

        // Render the grid
        println!("┌─────────────────────────────────────────────────────────────┐");
        for row in grid {
            println!("│ {:<61} │", row.iter().collect::<String>());
        }
        println!("└─────────────────────────────────────────────────────────────┘");

        Ok(())
    }

    fn calculate_floor_bounds(&self, floor: &Floor) -> (f64, f64, f64, f64) {
        // Returns (min_x, min_y, max_x, max_y) for top-down 2D floor plan view (X-Y plane)
        // Use ONLY polygon bounds - it's the authoritative floor plan shape
        let mut min_x = f64::INFINITY;
        let mut min_y = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut max_y = f64::NEG_INFINITY;
        let mut has_polygon = false;

        // Collect all rooms from wings
        let all_rooms: Vec<&Room> = floor
            .wings
            .iter()
            .flat_map(|wing| wing.rooms.iter())
            .collect();

        // Check polygon data first - this defines the floor plan coordinate space
        // Note: IFC polygon coordinates are in LOCAL space, AR scans use WORLD space
        for room in &all_rooms {
            if let Some(polygon_str) = room.properties.get("floor_polygon") {
                if !polygon_str.is_empty() {
                    has_polygon = true;
                    // Determine coordinate space
                    let is_world_space = room.properties.contains_key("scan_source")
                        || room.properties.contains_key("scan_mode");
                    let room_x = room.spatial_properties.position.x;
                    let room_y = room.spatial_properties.position.y;
                    for point_str in polygon_str.split(';') {
                        let parts: Vec<&str> = point_str.split(',').collect();
                        if parts.len() >= 2 {
                            if let (Ok(x_val), Ok(y_val)) =
                                (parts[0].parse::<f64>(), parts[1].parse::<f64>())
                            {
                                // Transform based on coordinate space
                                let x = if is_world_space {
                                    x_val
                                } else {
                                    x_val + room_x
                                };
                                let y = if is_world_space {
                                    y_val
                                } else {
                                    y_val + room_y
                                };
                                min_x = min_x.min(x);
                                min_y = min_y.min(y);
                                max_x = max_x.max(x);
                                max_y = max_y.max(y);
                            }
                        }
                    }
                }
            }
        }

        // Only fall back to bounding box if no polygon
        if !has_polygon {
            for room in &all_rooms {
                let bbox = &room.spatial_properties.bounding_box;
                min_x = min_x.min(bbox.min.x);
                min_y = min_y.min(bbox.min.y);
                max_x = max_x.max(bbox.max.x);
                max_y = max_y.max(bbox.max.y);
            }
        }

        // If no rooms, use equipment positions to calculate bounds
        if min_x == f64::INFINITY {
            for equipment in &floor.equipment {
                let eq_x = equipment.position.x;
                let eq_y = equipment.position.y;
                min_x = min_x.min(eq_x);
                min_y = min_y.min(eq_y);
                max_x = max_x.max(eq_x);
                max_y = max_y.max(eq_y);
            }
        }

        // Add small padding (or 10% if we have bounds)
        let padding = if min_x != f64::INFINITY {
            ((max_x - min_x).max(max_y - min_y) * 0.1).max(1.0)
        } else {
            0.1
        };
        (
            min_x - padding,
            min_y - padding,
            max_x + padding,
            max_y + padding,
        )
    }

    fn draw_room(
        &self,
        grid: &mut [Vec<char>],
        room: &Room,
        bounds: (f64, f64, f64, f64),
        _scale: f64,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let (min_x, min_y, max_x, max_y) = bounds;
        let grid_width = grid[0].len();
        let grid_height = grid.len();

        // Check if we have polygon data from the scan
        if let Some(polygon_str) = room.properties.get("floor_polygon") {
            if !polygon_str.is_empty() {
                // Parse polygon points: "x,y,z;x,y,z;..."
                // Determine coordinate space: IFC uses LOCAL, AR scans use WORLD
                let is_world_space = room.properties.contains_key("scan_source")
                    || room.properties.contains_key("scan_mode");

                let room_x = room.spatial_properties.position.x;
                let room_y = room.spatial_properties.position.y;
                let polygon_points: Vec<(f64, f64)> = polygon_str
                    .split(';')
                    .filter_map(|s| {
                        let parts: Vec<&str> = s.split(',').collect();
                        if parts.len() >= 2 {
                            let x_val = parts[0].parse::<f64>().ok()?;
                            let y_val = parts[1].parse::<f64>().ok()?;
                            // Transform based on coordinate space
                            let x = if is_world_space {
                                x_val
                            } else {
                                x_val + room_x
                            };
                            let y = if is_world_space {
                                y_val
                            } else {
                                y_val + room_y
                            };
                            // Polygon is in X-Y plane (Y is depth, Z is elevation)
                            Some((x, y))
                        } else {
                            None
                        }
                    })
                    .collect();

                if !polygon_points.is_empty() {
                    // Draw the actual polygon outline
                    self.draw_polygon_outline(
                        grid,
                        &polygon_points,
                        bounds,
                        grid_width,
                        grid_height,
                    )?;

                    // Draw room name in center
                    let (center_x, center_y) = self.calculate_polygon_center(
                        &polygon_points,
                        bounds,
                        grid_width,
                        grid_height,
                    );
                    self.draw_room_name(
                        grid,
                        &room.name,
                        center_x,
                        center_y,
                        grid_width,
                        grid_height,
                    );

                    return Ok(());
                }
            }
        }

        // Fallback to bounding box rectangle (X-Y plane)
        let bbox = &room.spatial_properties.bounding_box;
        let room_min_x = bbox.min.x;
        let room_min_y = bbox.min.y;
        let room_max_x = bbox.max.x;
        let room_max_y = bbox.max.y;

        let start_x = (((room_min_x - min_x) / (max_x - min_x) * grid_width as f64) as usize)
            .min(grid_width.saturating_sub(1));
        let end_x = (((room_max_x - min_x) / (max_x - min_x) * grid_width as f64) as usize)
            .min(grid_width.saturating_sub(1));
        let start_y = (((room_min_y - min_y) / (max_y - min_y) * grid_height as f64) as usize)
            .min(grid_height.saturating_sub(1));
        let end_y = (((room_max_y - min_y) / (max_y - min_y) * grid_height as f64) as usize)
            .min(grid_height.saturating_sub(1));

        let start_x = start_x.min(end_x);
        let start_y = start_y.min(end_y);
        let end_x = end_x.max(start_x);
        let end_y = end_y.max(start_y);

        // Draw rectangle
        #[allow(clippy::needless_range_loop)]
        for y in start_y..=end_y {
            for x in start_x..=end_x {
                if x < grid_width && y < grid_height {
                    let is_top = y == start_y;
                    let is_bottom = y == end_y;
                    let is_left = x == start_x;
                    let is_right = x == end_x;

                    let char = if is_top && is_left {
                        '┌'
                    } else if is_top && is_right {
                        '┐'
                    } else if is_bottom && is_left {
                        '└'
                    } else if is_bottom && is_right {
                        '┘'
                    } else if is_top || is_bottom {
                        '─'
                    } else if is_left || is_right {
                        '│'
                    } else {
                        ' '
                    };

                    grid[y][x] = char;
                }
            }
        }

        // Draw name
        let center_x = (start_x + end_x) / 2;
        let center_y = (start_y + end_y) / 2;
        self.draw_room_name(
            grid,
            &room.name,
            center_x,
            center_y,
            grid_width,
            grid_height,
        );

        Ok(())
    }

    fn draw_polygon_outline(
        &self,
        grid: &mut [Vec<char>],
        points: &[(f64, f64)],
        bounds: (f64, f64, f64, f64),
        grid_width: usize,
        grid_height: usize,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let (min_x, min_y, max_x, max_y) = bounds;

        // Convert polygon points to grid coordinates (X-Y plane)
        // Note: Flip Y-axis so larger Y values (further back) appear at top of screen
        let grid_points: Vec<(usize, usize)> = points
            .iter()
            .map(|(x, y)| {
                let gx = (((x - min_x) / (max_x - min_x) * grid_width as f64) as usize)
                    .min(grid_width.saturating_sub(1));
                // Flip Y: larger world Y should be at top (smaller screen Y)
                let gy = grid_height.saturating_sub(1)
                    - (((*y - min_y) / (max_y - min_y) * grid_height as f64) as usize)
                        .min(grid_height.saturating_sub(1));
                (gx, gy)
            })
            .collect();

        // Fill polygon interior FIRST (simple scanline fill)
        for (y, row) in grid.iter_mut().enumerate().take(grid_height) {
            let mut intersections = Vec::new();
            for i in 0..grid_points.len() {
                let p1 = grid_points[i];
                let p2 = grid_points[(i + 1) % grid_points.len()];

                let y1 = p1.1.min(p2.1);
                let y2 = p1.1.max(p2.1);

                if y >= y1 && y < y2 && y1 != y2 {
                    let x = (p1.0 as f64
                        + (y as f64 - p1.1 as f64) * (p2.0 as f64 - p1.0 as f64)
                            / (p2.1 as f64 - p1.1 as f64)) as usize;
                    intersections.push(x.min(grid_width.saturating_sub(1)));
                }
            }

            intersections.sort();
            intersections.dedup();
            for pair in intersections.chunks(2) {
                if pair.len() == 2 {
                    let start = pair[0].min(pair[1]);
                    let end = pair[0].max(pair[1]);
                    let end = end.min(grid_width.saturating_sub(1));
                    for cell in row.iter_mut().take(end + 1).skip(start) {
                        if *cell == ' ' {
                            *cell = '·';
                        }
                    }
                }
            }
        }

        // Draw polygon edges as walls AFTER fill (so walls appear on top)
        // The polygon outline IS the primary wall structure
        for i in 0..grid_points.len() {
            let p1 = grid_points[i];
            let p2 = if i + 1 < grid_points.len() {
                grid_points[i + 1]
            } else {
                grid_points[0] // Close the polygon
            };

            // Draw as wall line (this is the perimeter)
            self.draw_line(grid, p1, p2, grid_width, grid_height);
        }

        Ok(())
    }

    fn draw_line(
        &self,
        grid: &mut [Vec<char>],
        p1: (usize, usize),
        p2: (usize, usize),
        grid_width: usize,
        grid_height: usize,
    ) {
        let dx = (p2.0 as i32 - p1.0 as i32).abs();
        let dy = (p2.1 as i32 - p1.1 as i32).abs();
        let sx = if p1.0 < p2.0 { 1 } else { -1 };
        let sy = if p1.1 < p2.1 { 1 } else { -1 };
        let mut err = dx - dy;

        let mut x = p1.0 as i32;
        let mut y = p1.1 as i32;

        loop {
            if x >= 0 && x < grid_width as i32 && y >= 0 && y < grid_height as i32 {
                let current_char = grid[y as usize][x as usize];

                // Choose character based on line direction
                let char = if (x == p1.0 as i32 && y == p1.1 as i32)
                    || (x == p2.0 as i32 && y == p2.1 as i32)
                {
                    // Endpoints - use corner if diagonal, or continue line
                    if dx > 0 && dy > 0 {
                        '+'
                    } else if dx == 0 {
                        '│'
                    } else {
                        '─'
                    }
                } else if dx > dy * 2 {
                    '─' // Horizontal line
                } else if dy > dx * 2 {
                    '│' // Vertical line
                } else {
                    '/' // Diagonal (fallback)
                };

                // Overwrite space or dots, but merge with existing walls
                if current_char == ' ' || current_char == '·' {
                    grid[y as usize][x as usize] = char;
                } else if (current_char == '─' || current_char == '│' || current_char == '+')
                    && (char == '─' || char == '│')
                {
                    // Merge wall segments
                    if (current_char == '─' && char == '│') || (current_char == '│' && char == '─')
                    {
                        grid[y as usize][x as usize] = '+'; // Intersection
                    }
                }
            }

            if x == p2.0 as i32 && y == p2.1 as i32 {
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
    }

    fn calculate_polygon_center(
        &self,
        points: &[(f64, f64)],
        bounds: (f64, f64, f64, f64),
        grid_width: usize,
        grid_height: usize,
    ) -> (usize, usize) {
        let (min_x, min_y, max_x, max_y) = bounds;
        let (avg_x, avg_y) = points
            .iter()
            .fold((0.0, 0.0), |acc, p| (acc.0 + p.0, acc.1 + p.1));
        let n = points.len() as f64;
        let gx = (((avg_x / n - min_x) / (max_x - min_x) * grid_width as f64) as usize)
            .min(grid_width.saturating_sub(1));
        // Flip Y-axis to match polygon rendering
        let gy = grid_height.saturating_sub(1)
            - (((avg_y / n - min_y) / (max_y - min_y) * grid_height as f64) as usize)
                .min(grid_height.saturating_sub(1));
        (gx, gy)
    }

    fn draw_room_name(
        &self,
        grid: &mut [Vec<char>],
        name: &str,
        center_x: usize,
        center_y: usize,
        grid_width: usize,
        grid_height: usize,
    ) {
        if center_y < grid_height && center_x < grid_width {
            let name_start = center_x.saturating_sub(name.len() / 2);
            for (i, ch) in name
                .chars()
                .enumerate()
                .take(grid_width.saturating_sub(name_start))
            {
                let x = name_start + i;
                if x < grid_width && center_y < grid_height {
                    let current = grid[center_y][x];
                    if current == ' ' || current == '·' {
                        grid[center_y][x] = ch;
                    }
                }
            }
        }
    }

    fn draw_walls_in_polygon_space(
        &self,
        grid: &mut [Vec<char>],
        walls_str: &str,
        bounds: (f64, f64, f64, f64),
        grid_width: usize,
        grid_height: usize,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let (min_x, min_y, max_x, max_y) = bounds;
        let bounds_width = max_x - min_x;
        let bounds_height = max_y - min_y;

        // Only draw walls that are clearly within polygon coordinate space
        // Filter out walls that are in completely different coordinate systems

        // Parse wall segments
        for wall_str in walls_str.split('|') {
            let parts: Vec<&str> = wall_str.split(',').collect();
            if parts.len() >= 4 {
                if let (Ok(x1), Ok(y1), Ok(x2), Ok(y2)) = (
                    parts[0].parse::<f64>(),
                    parts[1].parse::<f64>(),
                    parts[2].parse::<f64>(),
                    parts[3].parse::<f64>(),
                ) {
                    // Check if wall is in polygon coordinate space
                    // (within reasonable distance of polygon bounds)
                    let margin = bounds_width.max(bounds_height) * 0.1; // 10% margin
                    let in_bounds = x1 >= (min_x - margin)
                        && x1 <= (max_x + margin)
                        && x2 >= (min_x - margin)
                        && x2 <= (max_x + margin)
                        && y1 >= (min_y - margin)
                        && y1 <= (max_y + margin)
                        && y2 >= (min_y - margin)
                        && y2 <= (max_y + margin);

                    if in_bounds {
                        // Clamp to bounds
                        let cx1 = x1.max(min_x).min(max_x);
                        let cy1 = y1.max(min_y).min(max_y);
                        let cx2 = x2.max(min_x).min(max_x);
                        let cy2 = y2.max(min_y).min(max_y);

                        // Convert to grid
                        let gx1 = (((cx1 - min_x) / bounds_width * grid_width as f64) as usize)
                            .min(grid_width.saturating_sub(1));
                        // Flip Y-axis to match polygon rendering
                        let gy1 = grid_height.saturating_sub(1)
                            - (((cy1 - min_y) / bounds_height * grid_height as f64) as usize)
                                .min(grid_height.saturating_sub(1));
                        let gx2 = (((cx2 - min_x) / bounds_width * grid_width as f64) as usize)
                            .min(grid_width.saturating_sub(1));
                        let gy2 = grid_height.saturating_sub(1)
                            - (((cy2 - min_y) / bounds_height * grid_height as f64) as usize)
                                .min(grid_height.saturating_sub(1));

                        if gx1 != gx2 || gy1 != gy2 {
                            self.draw_line(grid, (gx1, gy1), (gx2, gy2), grid_width, grid_height);
                        }
                    }
                }
            }
        }

        Ok(())
    }

    fn draw_equipment(
        &self,
        grid: &mut [Vec<char>],
        equipment: &Equipment,
        bounds: (f64, f64, f64, f64),
        _scale: f64,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let (min_x, min_y, max_x, max_y) = bounds;
        let width = grid[0].len();
        let height = grid.len();

        // Convert equipment position to grid coordinates (X-Y plane for 2D floor plan)
        let eq_x = (((equipment.position.x - min_x) / (max_x - min_x) * width as f64) as usize)
            .min(width.saturating_sub(1));
        // Flip Y-axis to match polygon rendering (larger world Y = smaller screen Y)
        let eq_y = height.saturating_sub(1)
            - (((equipment.position.y - min_y) / (max_y - min_y) * height as f64) as usize)
                .min(height.saturating_sub(1));

        // Draw equipment symbol based on type
        let symbol = self.get_equipment_symbol(equipment);

        if eq_y < height && eq_x < width {
            grid[eq_y][eq_x] = symbol;
        }

        Ok(())
    }

    fn get_equipment_symbol(&self, equipment: &Equipment) -> char {
        // Get system type from equipment type
        let system_type = match equipment.equipment_type {
            EquipmentType::HVAC => "HVAC",
            EquipmentType::Electrical => "ELECTRICAL",
            EquipmentType::Plumbing => "PLUMBING",
            EquipmentType::Safety => "SAFETY",
            EquipmentType::Network => "NETWORK",
            EquipmentType::AV => "AV",
            EquipmentType::Furniture => "FURNITURE",
            EquipmentType::Other(_) => "OTHER",
        };
        match system_type {
            "HVAC" => 'H',
            "ELECTRICAL" => 'E',
            "PLUMBING" => 'P',
            "LIGHTS" => 'L',
            "SAFETY" => 'S',
            "STRUCTURAL" => 'T',
            "ARCHITECTURAL" => 'A',
            _ => '?',
        }
    }

    fn render_equipment_summary(&self, floor: &Floor) -> Result<(), Box<dyn std::error::Error>> {
        let mut healthy = 0;
        let mut warnings = 0;
        let mut critical = 0;

        for equipment in &floor.equipment {
            // Map EquipmentStatus to health status
            let fallback = match equipment.status {
                EquipmentStatus::Active => Some(EquipmentHealthStatus::Healthy),
                EquipmentStatus::Maintenance => Some(EquipmentHealthStatus::Warning),
                EquipmentStatus::Inactive | EquipmentStatus::OutOfOrder => {
                    Some(EquipmentHealthStatus::Critical)
                }
                EquipmentStatus::Unknown => Some(EquipmentHealthStatus::Unknown),
            };
            let health_status = equipment.health_status.or(fallback);

            match health_status {
                Some(EquipmentHealthStatus::Healthy) => healthy += 1,
                Some(EquipmentHealthStatus::Warning) => warnings += 1,
                Some(EquipmentHealthStatus::Critical) => critical += 1,
                Some(EquipmentHealthStatus::Unknown) | None => warnings += 1,
            }
        }

        println!(
            "\nEquipment Status: ✅ {} healthy | ⚠️ {} warnings | ❌ {} critical",
            healthy, warnings, critical
        );
        println!("Last Updated: {}", chrono::Utc::now().format("%H:%M:%S"));
        println!("Data Source: YAML building data");

        // Show equipment details
        if !floor.equipment.is_empty() {
            println!("\nEquipment Details:");
            for equipment in &floor.equipment {
                let fallback = match equipment.status {
                    EquipmentStatus::Active => Some(EquipmentHealthStatus::Healthy),
                    EquipmentStatus::Maintenance => Some(EquipmentHealthStatus::Warning),
                    EquipmentStatus::Inactive | EquipmentStatus::OutOfOrder => {
                        Some(EquipmentHealthStatus::Critical)
                    }
                    EquipmentStatus::Unknown => Some(EquipmentHealthStatus::Unknown),
                };
                let health_status = equipment.health_status.or(fallback);
                let status_icon = self.get_status_symbol_from_health(health_status);
                let system_type = match equipment.equipment_type {
                    EquipmentType::HVAC => "HVAC",
                    EquipmentType::Electrical => "ELECTRICAL",
                    EquipmentType::Plumbing => "PLUMBING",
                    EquipmentType::Safety => "SAFETY",
                    EquipmentType::Network => "NETWORK",
                    EquipmentType::AV => "AV",
                    EquipmentType::Furniture => "FURNITURE",
                    EquipmentType::Other(_) => "OTHER",
                };
                println!(
                    "  {} {} ({}) - {}",
                    status_icon, equipment.name, system_type, equipment.path
                );
            }
        }

        Ok(())
    }

    fn get_status_symbol_from_health(&self, health_status: Option<EquipmentHealthStatus>) -> &str {
        match health_status {
            Some(EquipmentHealthStatus::Healthy) => "✅",
            Some(EquipmentHealthStatus::Warning) => "⚠️",
            Some(EquipmentHealthStatus::Critical) => "❌",
            Some(EquipmentHealthStatus::Unknown) | None => "❓",
        }
    }
}
