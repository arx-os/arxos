//! Progressive ASCII renderer for slow-bleed detail accumulation

use heapless::String;
use crate::{ArxObject, DetailLevel, DetailStore, object_types};

/// ASCII renderer that shows progressively more detail
pub struct ProgressiveRenderer {
    /// ASCII art templates at different detail levels
    templates: TemplateStore,
    
    /// Current view settings
    pub show_connections: bool,
    pub show_analytics: bool,
    pub show_predictions: bool,
}

/// Stores ASCII art templates for different object types
struct TemplateStore;

impl ProgressiveRenderer {
    pub fn new() -> Self {
        Self {
            templates: TemplateStore,
            show_connections: true,
            show_analytics: false,
            show_predictions: false,
        }
    }
    
    /// Render an object with its current detail level
    pub fn render_object(
        &self,
        object: &ArxObject,
        detail_level: &DetailLevel,
    ) -> String<1024> {
        let mut output = String::new();
        
        // Select rendering based on completeness
        let completeness = detail_level.completeness();
        
        if completeness < 0.2 {
            self.render_basic(object, &mut output);
        } else if completeness < 0.5 {
            self.render_intermediate(object, detail_level, &mut output);
        } else if completeness < 0.8 {
            self.render_detailed(object, detail_level, &mut output);
        } else {
            self.render_cad_level(object, detail_level, &mut output);
        }
        
        output
    }
    
    /// Basic rendering - just position and type
    fn render_basic(&self, object: &ArxObject, output: &mut String<1024>) {
        use core::fmt::Write;
        
        let type_char = match object.object_type {
            object_types::OUTLET => 'o',
            object_types::LIGHT_SWITCH => 's',
            object_types::THERMOSTAT => 't',
            object_types::DOOR => 'D',
            object_types::WINDOW => 'W',
            object_types::CAMERA => 'C',
            object_types::ROOM => 'R',
            object_types::WIFI_AP => '@',
            _ => '?',
        };
        
        let _ = write!(
            output,
            "[{}] {:04X} @ ({},{},{})",
            type_char,
            object.id,
            object.x / 1000,  // Convert mm to m
            object.y / 1000,
            object.z / 1000
        );
    }
    
    /// Intermediate rendering - basic ASCII art
    fn render_intermediate(
        &self,
        object: &ArxObject,
        detail_level: &DetailLevel,
        output: &mut String<1024>
    ) {
        use core::fmt::Write;
        
        // Add basic ASCII representation
        match object.object_type {
            object_types::OUTLET => {
                let _ = write!(output, 
                    " ___\n\
                     |o o|\n\
                     |___|\n\
                     {:04X}", object.id);
            }
            object_types::LIGHT_SWITCH => {
                let _ = write!(output,
                    " ___\n\
                     | | |\n\
                     |_|_|\n\
                     {:04X}", object.id);
            }
            object_types::THERMOSTAT => {
                let temp = object.properties[0];
                let _ = write!(output,
                    " ____\n\
                     |{:3}°|\n\
                     |____|\n\
                     {:04X}", temp, object.id);
            }
            object_types::DOOR => {
                let _ = write!(output,
                    " ____\n\
                     |    |\n\
                     | () |\n\
                     |    |\n\
                     |____|\n\
                     {:04X}", object.id);
            }
            _ => self.render_basic(object, output),
        }
        
        // Add material info if available
        if detail_level.material > 0.0 {
            let _ = write!(output, "\n Mat: {:.0}%", detail_level.material * 100.0);
        }
    }
    
    /// Detailed rendering - includes connections and properties
    fn render_detailed(
        &self,
        object: &ArxObject,
        detail_level: &DetailLevel,
        output: &mut String<1024>
    ) {
        use core::fmt::Write;
        
        // Start with intermediate art
        self.render_intermediate(object, detail_level, output);
        
        // Add system connections if available
        if detail_level.systems > 0.0 && self.show_connections {
            let _ = write!(output, "\n\nConnections:");
            
            match object.object_type {
                object_types::OUTLET => {
                    let circuit = object.properties[0];
                    let voltage = u16::from_le_bytes([object.properties[1], object.properties[2]]);
                    let _ = write!(output, "\n  Circuit: {}", circuit);
                    let _ = write!(output, "\n  Voltage: {}V", voltage);
                }
                object_types::THERMOSTAT => {
                    let zone = object.properties[1];
                    let _ = write!(output, "\n  HVAC Zone: {}", zone);
                    let _ = write!(output, "\n  Mode: Heat/Cool");
                }
                _ => {}
            }
        }
        
        // Add historical data if available
        if detail_level.historical > 0.0 && self.show_analytics {
            let _ = write!(output, "\n\nHistory:");
            let _ = write!(output, "\n  Data: {:.0}%", detail_level.historical * 100.0);
        }
    }
    
    /// CAD-level rendering - full ASCII art with all details
    fn render_cad_level(
        &self,
        object: &ArxObject,
        detail_level: &DetailLevel,
        output: &mut String<1024>
    ) {
        use core::fmt::Write;
        
        // Rich ASCII art based on type
        match object.object_type {
            object_types::OUTLET => {
                let circuit = object.properties[0];
                let voltage = u16::from_le_bytes([object.properties[1], object.properties[2]]);
                let amps = object.properties[3];
                
                let _ = write!(output,
                    "   ╔════════╗\n\
                     ║  ┌──┐  ┌──┐  ║\n\
                     ║  │  │  │  │  ║ {}V\n\
                     ║  └──┘  └──┘  ║ {}A\n\
                     ╚════════╝\n\
                     ID: {:04X} | Circuit {}\n",
                    voltage, amps, object.id, circuit);
                
                if detail_level.predictive > 0.0 && self.show_predictions {
                    let _ = write!(output, "⚡ Load prediction: Normal\n");
                    let _ = write!(output, "🔧 Next maintenance: 180 days\n");
                }
            }
            object_types::THERMOSTAT => {
                let temp = object.properties[0];
                let setpoint = object.properties[1];
                let zone = object.properties[2];
                
                let _ = write!(output,
                    "  ╔═══════════╗\n\
                     ║  ┌─────┐  ║\n\
                     ║  │ {:3}° │  ║ Current\n\
                     ║  │ ─── │  ║\n\
                     ║  │ {:3}° │  ║ Setpoint\n\
                     ║  └─────┘  ║\n\
                     ║  [▲] [▼]  ║\n\
                     ╚═══════════╝\n\
                     ID: {:04X} | Zone {}\n",
                    temp, setpoint, object.id, zone);
                
                if detail_level.simulation > 0.0 {
                    let _ = write!(output, "📊 Thermal model: Active\n");
                    let _ = write!(output, "💨 Airflow: Balanced\n");
                }
            }
            object_types::ELECTRICAL_PANEL => {
                let _ = write!(output,
                    "  ╔═══════════════╗\n\
                     ║ ┌─┬─┬─┬─┬─┬─┐ ║\n\
                     ║ │1│2│3│4│5│6│ ║\n\
                     ║ ├─┼─┼─┼─┼─┼─┤ ║\n\
                     ║ │7│8│9│A│B│C│ ║\n\
                     ║ ├─┼─┼─┼─┼─┼─┤ ║\n\
                     ║ │D│E│F│M│▓│▓│ ║\n\
                     ║ └─┴─┴─┴─┴─┴─┘ ║\n\
                     ╚═══════════════╝\n\
                     Panel {:04X}\n",
                    object.id);
                
                if detail_level.systems > 0.8 {
                    let _ = write!(output, "⚡ Total Load: 145A / 200A\n");
                    let _ = write!(output, "🔌 Active Circuits: 14/16\n");
                }
            }
            _ => self.render_detailed(object, detail_level, output),
        }
        
        // Add full detail stats
        let _ = write!(output, "\n╭─ Detail Level ─╮\n");
        let _ = write!(output, "│ Complete: {:3.0}% │\n", detail_level.completeness() * 100.0);
        
        if detail_level.material > 0.0 {
            let _ = write!(output, "│ Material: {:3.0}% │\n", detail_level.material * 100.0);
        }
        if detail_level.systems > 0.0 {
            let _ = write!(output, "│ Systems:  {:3.0}% │\n", detail_level.systems * 100.0);
        }
        if detail_level.historical > 0.0 {
            let _ = write!(output, "│ History:  {:3.0}% │\n", detail_level.historical * 100.0);
        }
        if detail_level.simulation > 0.0 {
            let _ = write!(output, "│ Sim Model:{:3.0}% │\n", detail_level.simulation * 100.0);
        }
        if detail_level.predictive > 0.0 {
            let _ = write!(output, "│ Predict:  {:3.0}% │\n", detail_level.predictive * 100.0);
        }
        
        let _ = write!(output, "╰────────────────╯");
    }
    
    /// Render a collection of objects as a floor plan
    pub fn render_floor_plan(
        &self,
        objects: &[(ArxObject, DetailLevel)],
        width: usize,
        height: usize,
    ) -> String<4096> {
        let mut output = String::new();
        use core::fmt::Write;
        
        // Create grid
        let mut grid = [[' '; 80]; 24];
        
        // Place objects on grid
        for (object, _detail) in objects {
            let x = ((object.x as usize * width) / 65535).min(width - 1);
            let y = ((object.y as usize * height) / 65535).min(height - 1);
            
            let symbol = match object.object_type {
                object_types::OUTLET => 'o',
                object_types::LIGHT_SWITCH => 's',
                object_types::THERMOSTAT => 't',
                object_types::DOOR => 'D',
                object_types::WINDOW => 'W',
                object_types::CAMERA => 'C',
                object_types::ROOM => '□',
                object_types::WIFI_AP => '@',
                object_types::ELECTRICAL_PANEL => '⚡',
                _ => '?',
            };
            
            if x < 80 && y < 24 {
                grid[y][x] = symbol;
            }
        }
        
        // Draw grid
        let _ = write!(output, "┌");
        for _ in 0..width { let _ = write!(output, "─"); }
        let _ = write!(output, "┐\n");
        
        for row in 0..height.min(24) {
            let _ = write!(output, "│");
            for col in 0..width.min(80) {
                let _ = write!(output, "{}", grid[row][col]);
            }
            let _ = write!(output, "│\n");
        }
        
        let _ = write!(output, "└");
        for _ in 0..width { let _ = write!(output, "─"); }
        let _ = write!(output, "┘\n");
        
        output
    }
}

/// Render a progress bar for detail accumulation
pub fn render_progress_bar(completeness: f32, width: usize) -> String<128> {
    let mut output = String::new();
    use core::fmt::Write;
    
    let filled = ((completeness * width as f32) as usize).min(width);
    let empty = width - filled;
    
    let _ = write!(output, "[");
    for _ in 0..filled { let _ = write!(output, "█"); }
    for _ in 0..empty { let _ = write!(output, "░"); }
    let _ = write!(output, "] {:.0}%", completeness * 100.0);
    
    output
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_rendering() {
        let renderer = ProgressiveRenderer::new();
        let object = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, 1500);
        let detail = DetailLevel::default();
        
        let output = renderer.render_object(&object, &detail);
        assert!(output.contains("1234"));
    }
    
    #[test]
    fn test_progress_bar() {
        let bar = render_progress_bar(0.5, 10);
        assert!(bar.contains("█████"));
        assert!(bar.contains("░░░░░"));
        assert!(bar.contains("50%"));
    }
}