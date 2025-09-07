//! Terminal interface for ArxOS

use crate::models::Building;
use crate::query::QueryEngine;
use anyhow::Result;
use rustyline::DefaultEditor;
use std::collections::HashSet;

pub struct Terminal {
    building: Building,
    cwd: String,  // Current working directory
}

impl Terminal {
    pub fn new(building: Building) -> Self {
        Self {
            building,
            cwd: "/".to_string(),
        }
    }
    
    pub async fn run(&mut self) -> Result<()> {
        let mut rl = DefaultEditor::new()?;
        
        loop {
            let prompt = format!("arxos:{}> ", self.cwd);
            
            match rl.readline(&prompt) {
                Ok(line) => {
                    let line = line.trim();
                    if line.is_empty() {
                        continue;
                    }
                    
                    rl.add_history_entry(line);
                    
                    if line.eq_ignore_ascii_case("exit") || line.eq_ignore_ascii_case("quit") {
                        println!("Goodbye!");
                        break;
                    }
                    
                    if let Err(e) = self.execute(line) {
                        eprintln!("Error: {}", e);
                    }
                }
                Err(_) => break,
            }
        }
        
        Ok(())
    }
    
    pub fn execute(&mut self, command: &str) -> Result<()> {
        let parts: Vec<&str> = command.split_whitespace().collect();
        if parts.is_empty() {
            return Ok(());
        }
        
        let cmd = parts[0].to_uppercase();
        let args = &parts[1..];
        
        match cmd.as_str() {
            "CD" => self.cmd_cd(args),
            "LS" | "LIST" => self.cmd_ls(args),
            "LOOK" => self.cmd_look(args),
            "PWD" => self.cmd_pwd(),
            "INSPECT" => self.cmd_inspect(args),
            "TRACE" => self.cmd_trace(args),
            "NEAR" => self.cmd_near(args),
            "SELECT" => self.cmd_select(command),
            "HELP" => self.cmd_help(),
            _ => {
                if command.to_uppercase().starts_with("SELECT") {
                    self.cmd_select(command)
                } else {
                    println!("Unknown command: {}. Type HELP for commands.", cmd);
                    Ok(())
                }
            }
        }
    }
    
    fn cmd_cd(&mut self, args: &[&str]) -> Result<()> {
        if args.is_empty() {
            self.cwd = "/".to_string();
            return Ok(());
        }
        
        let target = args[0];
        
        if target == "/" {
            self.cwd = "/".to_string();
        } else if target == ".." {
            let parts: Vec<&str> = self.cwd.split('/').filter(|s| !s.is_empty()).collect();
            if !parts.is_empty() {
                let new_path = parts[..parts.len() - 1].join("/");
                self.cwd = if new_path.is_empty() {
                    "/".to_string()
                } else {
                    format!("/{}", new_path)
                };
            }
        } else {
            let new_path = if target.starts_with('/') {
                target.to_string()
            } else if self.cwd == "/" {
                format!("/{}", target)
            } else {
                format!("{}/{}", self.cwd, target)
            };
            
            // Check if path exists
            if self.path_exists(&new_path) {
                self.cwd = new_path;
            } else {
                println!("Path not found: {}", new_path);
            }
        }
        
        Ok(())
    }
    
    fn cmd_ls(&self, args: &[&str]) -> Result<()> {
        let path = if args.is_empty() {
            &self.cwd
        } else {
            args[0]
        };
        
        let objects = self.building.list_at_path(path);
        
        if objects.is_empty() {
            println!("(empty)");
        } else {
            // Group by directory
            let mut dirs = HashSet::new();
            let mut files = Vec::new();
            
            let prefix = if path == "/" {
                "/".to_string()
            } else {
                format!("{}/", path)
            };
            
            for obj in objects {
                if obj.path.starts_with(&prefix) {
                    let remainder = &obj.path[prefix.len()..];
                    if let Some(slash_pos) = remainder.find('/') {
                        dirs.insert(&remainder[..slash_pos]);
                    } else {
                        files.push(obj);
                    }
                }
            }
            
            // Print directories
            for dir in dirs {
                println!("  {}/", dir);
            }
            
            // Print objects
            for obj in files {
                let status = if obj.state.needs_repair {
                    " [NEEDS REPAIR]"
                } else if obj.state.status == "failed" {
                    " [FAILED]"
                } else {
                    ""
                };
                println!("  {}{}", obj.name(), status);
            }
        }
        
        Ok(())
    }
    
    fn cmd_look(&self, _args: &[&str]) -> Result<()> {
        println!("Current location: {}", self.cwd);
        
        let objects = self.building.list_at_path(&self.cwd);
        
        if !objects.is_empty() {
            println!("\nYou see:");
            for obj in objects.iter().take(10) {
                println!("  - {} ({})", obj.name(), obj.object_type);
            }
            if objects.len() > 10 {
                println!("  ... and {} more", objects.len() - 10);
            }
        }
        
        Ok(())
    }
    
    fn cmd_pwd(&self) -> Result<()> {
        println!("{}", self.cwd);
        Ok(())
    }
    
    fn cmd_inspect(&self, args: &[&str]) -> Result<()> {
        if args.is_empty() {
            println!("Usage: INSPECT <object>");
            return Ok(());
        }
        
        let target = args[0];
        let path = if target.starts_with('/') {
            target.to_string()
        } else if self.cwd == "/" {
            format!("/{}", target)
        } else {
            format!("{}/{}", self.cwd, target)
        };
        
        if let Some(obj) = self.building.find_by_path(&path) {
            println!("╔════════════════════════════════════════════╗");
            println!("║ Object: {:<34} ║", obj.name());
            println!("╚════════════════════════════════════════════╝");
            println!();
            println!("Path:     {}", obj.path);
            println!("Type:     {}", obj.object_type);
            println!("Status:   {}", obj.state.status);
            println!("Health:   {}", obj.state.health);
            
            if obj.state.needs_repair {
                println!("\n⚠ NEEDS REPAIR");
            }
            
            if !obj.properties.is_empty() {
                println!("\nProperties:");
                for (key, value) in &obj.properties {
                    println!("  {}: {}", key, value);
                }
            }
            
            if !obj.state.metrics.is_empty() {
                println!("\nMetrics:");
                for (key, value) in &obj.state.metrics {
                    println!("  {}: {}", key, value);
                }
            }
        } else {
            println!("Object not found: {}", path);
        }
        
        Ok(())
    }
    
    fn cmd_trace(&self, args: &[&str]) -> Result<()> {
        if args.len() < 2 {
            println!("Usage: TRACE <object> <UPSTREAM|DOWNSTREAM>");
            return Ok(());
        }
        
        let target = args[0];
        let direction = args[1].to_uppercase();
        
        let path = if target.starts_with('/') {
            target.to_string()
        } else if self.cwd == "/" {
            format!("/{}", target)
        } else {
            format!("{}/{}", self.cwd, target)
        };
        
        if let Some(obj) = self.building.find_by_path(&path) {
            println!("Tracing {} from {}:", direction.to_lowercase(), obj.name());
            
            // Simple trace implementation
            if direction == "UPSTREAM" {
                let mut current = obj;
                let mut depth = 0;
                
                while let Some(parent_id) = current.parent_id {
                    if let Some(parent) = self.building.get_object(&parent_id) {
                        println!("{}→ {}", "  ".repeat(depth), parent.name());
                        current = parent;
                        depth += 1;
                        
                        if depth > 10 {
                            println!("  ... (trace limited to 10 levels)");
                            break;
                        }
                    } else {
                        break;
                    }
                }
            } else {
                println!("  (downstream trace not yet implemented)");
            }
        } else {
            println!("Object not found: {}", path);
        }
        
        Ok(())
    }
    
    fn cmd_near(&self, args: &[&str]) -> Result<()> {
        let radius = if !args.is_empty() {
            args[0].parse::<f32>().unwrap_or(5.0)
        } else {
            5.0
        };
        
        // Find current object
        if let Some(current) = self.building.find_by_path(&self.cwd) {
            println!("Objects within {}m:", radius);
            
            for obj in self.building.objects.values() {
                if obj.id != current.id {
                    let dx = obj.location.x - current.location.x;
                    let dy = obj.location.y - current.location.y;
                    let dz = obj.location.z - current.location.z;
                    let distance = (dx * dx + dy * dy + dz * dz).sqrt();
                    
                    if distance <= radius {
                        println!("  {} - {:.1}m away", obj.name(), distance);
                    }
                }
            }
        } else {
            println!("Set your location first with CD");
        }
        
        Ok(())
    }
    
    fn cmd_select(&self, query: &str) -> Result<()> {
        let query_engine = QueryEngine::new(&self.building);
        let results = query_engine.execute(query)?;
        
        println!("Found {} objects:", results.len());
        for obj in results.iter().take(20) {
            println!("  {} - {} ({})", obj.path, obj.object_type, obj.state.status);
        }
        
        if results.len() > 20 {
            println!("  ... and {} more", results.len() - 20);
        }
        
        Ok(())
    }
    
    fn cmd_help(&self) -> Result<()> {
        println!("ArxOS Terminal Commands");
        println!("═══════════════════════");
        println!();
        println!("Navigation:");
        println!("  CD <path>           - Change directory");
        println!("  LS [path]           - List directory contents");
        println!("  PWD                 - Print working directory");
        println!("  LOOK                - Describe current location");
        println!();
        println!("Inspection:");
        println!("  INSPECT <object>    - Show detailed object info");
        println!("  TRACE <obj> <dir>   - Trace connections");
        println!("  NEAR [radius]       - Find nearby objects");
        println!();
        println!("Queries:");
        println!("  SELECT * FROM objects WHERE <condition>");
        println!();
        println!("Other:");
        println!("  HELP                - Show this help");
        println!("  EXIT                - Exit terminal");
        
        Ok(())
    }
    
    fn path_exists(&self, path: &str) -> bool {
        self.building.find_by_path(path).is_some() ||
        self.building.objects.values().any(|o| o.path.starts_with(path))
    }
}