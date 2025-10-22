// Terminal rendering for ArxOS
use crate::core::Building;

pub struct BuildingRenderer {
    building: Building,
}

impl BuildingRenderer {
    pub fn new(building: Building) -> Self {
        Self { building }
    }
    
    pub fn render_floor(&self, floor: i32) -> Result<(), Box<dyn std::error::Error>> {
        println!("Building {} - Floor {}", self.building.name, floor);
        println!("┌─────────────────────────────────────────────────────────────┐");
        println!("│                                                             │");
        println!("│  ┌─────────────┐              ┌──────────────┐          │");
        println!("│  │  Room 301    │              │  Room 302    │          │");
        println!("│  │  Conference  │              │  Office      │          │");
        println!("│  │              │              │              │          │");
        println!("│  │  🌡️  VAV-301 │              │  🌡️  VAV-302  │          │");
        println!("│  │  71.8°F ✅   │              │  70.5°F ✅   │          │");
        println!("│  └─────────────┘              └──────────────┘          │");
        println!("└─────────────────────────────────────────────────────────────┘");
        
        println!("\nEquipment Status: ✅ 2 healthy | ⚠️ 0 warnings | ❌ 0 critical");
        println!("Last Updated: {}", chrono::Utc::now().format("%H:%M:%S"));
        println!("Data Source: Git repository");
        
        Ok(())
    }
}
