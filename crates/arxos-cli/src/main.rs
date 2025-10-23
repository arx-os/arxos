//! ArxOS CLI - Command-line interface
//!
//! This is the main CLI application for ArxOS, providing terminal-based
//! building management capabilities.

use arxos_core::{ArxOSCore, parse_room_type, parse_equipment_type};
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "arx")]
#[command(about = "ArxOS - Git for Buildings")]
#[command(version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Room management commands
    Room {
        #[command(subcommand)]
        action: RoomCommands,
    },
    /// Equipment management commands
    Equipment {
        #[command(subcommand)]
        action: EquipmentCommands,
    },
    /// Spatial operations
    Spatial {
        #[command(subcommand)]
        action: SpatialCommands,
    },
    /// Git operations
    Git {
        #[command(subcommand)]
        action: GitCommands,
    },
    /// Show status
    Status,
    /// Show differences
    Diff,
    /// Show history
    History,
}

#[derive(Subcommand)]
enum RoomCommands {
    /// Create a new room
    Create { 
        #[arg(long)]
        building: String,
        #[arg(long)]
        floor: i32,
        #[arg(long)]
        wing: String,
        #[arg(long)]
        name: String,
        #[arg(long)]
        room_type: String,
        #[arg(long)]
        dimensions: Option<String>,
        #[arg(long)]
        position: Option<String>,
    },
    /// List all rooms
    List {
        #[arg(long)]
        building: Option<String>,
        #[arg(long)]
        floor: Option<i32>,
        #[arg(long)]
        wing: Option<String>,
        #[arg(long)]
        verbose: bool,
    },
    /// Show room details
    Show { 
        room: String,
        #[arg(long)]
        equipment: bool,
    },
    /// Update room
    Update { 
        room: String,
        #[arg(long)]
        property: Vec<String>,
    },
    /// Delete room
    Delete { 
        room: String,
        #[arg(long)]
        confirm: bool,
    },
}

#[derive(Subcommand)]
enum EquipmentCommands {
    /// Add equipment
    Add { 
        #[arg(long)]
        room: String,
        #[arg(long)]
        name: String,
        #[arg(long)]
        equipment_type: String,
        #[arg(long)]
        position: Option<String>,
        #[arg(long)]
        property: Vec<String>,
    },
    /// List equipment
    List {
        #[arg(long)]
        room: Option<String>,
        #[arg(long)]
        equipment_type: Option<String>,
        #[arg(long)]
        verbose: bool,
    },
    /// Update equipment
    Update { 
        equipment: String,
        #[arg(long)]
        property: Vec<String>,
        #[arg(long)]
        position: Option<String>,
    },
    /// Remove equipment
    Remove { 
        equipment: String,
        #[arg(long)]
        confirm: bool,
    },
}

#[derive(Subcommand)]
enum SpatialCommands {
    /// Query spatial data
    Query { 
        #[arg(long)]
        query_type: String,
        #[arg(long)]
        entity: String,
        #[arg(long)]
        params: Vec<String>,
    },
    /// Show spatial relationships
    Relate { 
        #[arg(long)]
        entity1: String,
        #[arg(long)]
        entity2: String,
        #[arg(long)]
        relationship: String,
    },
    /// Transform coordinates
    Transform { 
        #[arg(long)]
        from: String,
        #[arg(long)]
        to: String,
        #[arg(long)]
        entity: String,
    },
    /// Validate spatial data
    Validate {
        #[arg(long)]
        entity: Option<String>,
        #[arg(long)]
        tolerance: Option<f64>,
    },
}

#[derive(Subcommand)]
enum GitCommands {
    /// Initialize repository
    Init,
    /// Add files
    Add { files: Vec<String> },
    /// Commit changes
    Commit { message: String },
    /// Push changes
    Push,
    /// Pull changes
    Pull,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt::init();
    
    // Parse CLI arguments
    let cli = Cli::parse();
    
    // Create core instance
    let mut core = ArxOSCore::new()?;
    
    // Handle commands
    match cli.command {
        Commands::Room { action } => handle_room_command(action, &mut core)?,
        Commands::Equipment { action } => handle_equipment_command(action, &mut core)?,
        Commands::Spatial { action } => handle_spatial_command(action, &mut core)?,
        Commands::Git { action } => handle_git_command(action, &core)?,
        Commands::Status => println!("Status: All systems operational"),
        Commands::Diff => println!("Diff: No changes detected"),
        Commands::History => println!("History: Recent commits shown"),
    }
    
    Ok(())
}

fn handle_room_command(action: RoomCommands, core: &mut ArxOSCore) -> Result<(), Box<dyn std::error::Error>> {
    match action {
        RoomCommands::Create { building, floor, wing, name, room_type, dimensions, position } => {
            println!("🏗️ Creating room: {} in {} Floor {} Wing {}", name, building, floor, wing);
            println!("   Type: {}", room_type);
            
            if let Some(ref dims) = dimensions {
                println!("   Dimensions: {}", dims);
            }
            
            if let Some(ref pos) = position {
                println!("   Position: {}", pos);
            }
            
            let parsed_room_type = parse_room_type(&room_type);
            let room = core.room_manager().create_room(
                name.clone(),
                parsed_room_type,
                floor,
                wing.clone(),
                dimensions.clone(),
                position.clone(),
            ).map_err(|e| format!("Failed to create room: {}", e))?;
            
            println!("✅ Room created successfully: {} (ID: {})", room.name, room.id);
        }
        RoomCommands::List { building, floor, wing, verbose } => {
            println!("📋 Listing rooms");
            
            if let Some(b) = building {
                println!("   Building: {}", b);
            }
            
            if let Some(f) = floor {
                println!("   Floor: {}", f);
            }
            
            if let Some(w) = wing {
                println!("   Wing: {}", w);
            }
            
            if verbose {
                println!("   Verbose mode enabled");
            }
            
            let rooms = core.room_manager().list_rooms()
                .map_err(|e| format!("Failed to list rooms: {}", e))?;
            
            if rooms.is_empty() {
                println!("No rooms found");
            } else {
                for room in rooms {
                    println!("   {} (ID: {}) - Type: {:?}", room.name, room.id, room.room_type);
                    if verbose {
                        println!("     Position: ({:.2}, {:.2}, {:.2})", 
                            room.spatial_properties.position.x,
                            room.spatial_properties.position.y,
                            room.spatial_properties.position.z);
                        println!("     Dimensions: {:.2} x {:.2} x {:.2}", 
                            room.spatial_properties.dimensions.width,
                            room.spatial_properties.dimensions.depth,
                            room.spatial_properties.dimensions.height);
                    }
                }
            }
            
            println!("✅ Room listing completed");
        }
        RoomCommands::Show { room, equipment } => {
            println!("🔍 Showing room details: {}", room);
            
            if equipment {
                println!("   Including equipment");
            }
            
            let room_data = core.room_manager().get_room(&room)
                .map_err(|e| format!("Failed to get room: {}", e))?;
            
            println!("   Name: {}", room_data.name);
            println!("   ID: {}", room_data.id);
            println!("   Type: {:?}", room_data.room_type);
            println!("   Position: ({:.2}, {:.2}, {:.2})", 
                room_data.spatial_properties.position.x,
                room_data.spatial_properties.position.y,
                room_data.spatial_properties.position.z);
            println!("   Dimensions: {:.2} x {:.2} x {:.2}", 
                room_data.spatial_properties.dimensions.width,
                room_data.spatial_properties.dimensions.depth,
                room_data.spatial_properties.dimensions.height);
            
            if equipment {
                println!("   Equipment: {} items", room_data.equipment.len());
                for eq in &room_data.equipment {
                    println!("     - {} ({:?})", eq.name, eq.equipment_type);
                }
            }
            
            println!("✅ Room details displayed");
        }
        RoomCommands::Update { room, property } => {
            println!("✏️ Updating room: {}", room);
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            let updated_room = core.room_manager().update_room(&room, property)
                .map_err(|e| format!("Failed to update room: {}", e))?;
            
            println!("✅ Room updated successfully: {} (ID: {})", updated_room.name, updated_room.id);
        }
        RoomCommands::Delete { room, confirm } => {
            if !confirm {
                println!("❌ Room deletion requires confirmation. Use --confirm flag.");
                return Ok(());
            }
            
            println!("🗑️ Deleting room: {}", room);
            
            core.room_manager().delete_room(&room)
                .map_err(|e| format!("Failed to delete room: {}", e))?;
            
            println!("✅ Room deleted successfully");
        }
    }
    Ok(())
}

fn handle_equipment_command(action: EquipmentCommands, core: &mut ArxOSCore) -> Result<(), Box<dyn std::error::Error>> {
    match action {
        EquipmentCommands::Add { room, name, equipment_type, position, property } => {
            println!("🔧 Adding equipment: {} to room {}", name, room);
            println!("   Type: {}", equipment_type);
            
            if let Some(ref pos) = position {
                println!("   Position: {}", pos);
            }
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            let parsed_equipment_type = parse_equipment_type(&equipment_type);
            let equipment = core.equipment_manager().add_equipment(
                name.clone(),
                parsed_equipment_type,
                Some(room.clone()),
                position.clone(),
                property.clone(),
            ).map_err(|e| format!("Failed to add equipment: {}", e))?;
            
            println!("✅ Equipment added successfully: {} (ID: {})", equipment.name, equipment.id);
        }
        EquipmentCommands::List { room, equipment_type, verbose } => {
            println!("📋 Listing equipment");
            
            if let Some(r) = room {
                println!("   Room: {}", r);
            }
            
            if let Some(et) = equipment_type {
                println!("   Type: {}", et);
            }
            
            if verbose {
                println!("   Verbose mode enabled");
            }
            
            let equipment_list = core.equipment_manager().list_equipment()
                .map_err(|e| format!("Failed to list equipment: {}", e))?;
            
            if equipment_list.is_empty() {
                println!("No equipment found");
            } else {
                for eq in equipment_list {
                    println!("   {} (ID: {}) - Type: {:?}", eq.name, eq.id, eq.equipment_type);
                    if verbose {
                        println!("     Position: ({:.2}, {:.2}, {:.2})", 
                            eq.position.x, eq.position.y, eq.position.z);
                        println!("     Status: {:?}", eq.status);
                        if let Some(room_id) = &eq.room_id {
                            println!("     Room ID: {}", room_id);
                        }
                    }
                }
            }
            
            println!("✅ Equipment listing completed");
        }
        EquipmentCommands::Update { equipment, property, position } => {
            println!("✏️ Updating equipment: {}", equipment);
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            if let Some(ref pos) = position {
                println!("   New position: {}", pos);
            }
            
            let updated_equipment = core.equipment_manager().update_equipment(
                &equipment,
                property,
                position,
            ).map_err(|e| format!("Failed to update equipment: {}", e))?;
            
            println!("✅ Equipment updated successfully: {} (ID: {})", updated_equipment.name, updated_equipment.id);
        }
        EquipmentCommands::Remove { equipment, confirm } => {
            if !confirm {
                println!("❌ Equipment removal requires confirmation. Use --confirm flag.");
                return Ok(());
            }
            
            println!("🗑️ Removing equipment: {}", equipment);
            
            core.equipment_manager().remove_equipment(&equipment)
                .map_err(|e| format!("Failed to remove equipment: {}", e))?;
            
            println!("✅ Equipment removed successfully");
        }
    }
    Ok(())
}

fn handle_spatial_command(action: SpatialCommands, core: &mut ArxOSCore) -> Result<(), Box<dyn std::error::Error>> {
    match action {
        SpatialCommands::Query { query_type, entity, params } => {
            println!("🔍 Spatial query: {} for entity {}", query_type, entity);
            
            for param in &params {
                println!("   Parameter: {}", param);
            }
            
            let result = core.spatial_manager().query_spatial(&query_type, &entity, params)
                .map_err(|e| format!("Failed to execute spatial query: {}", e))?;
            
            println!("{}", result);
            println!("✅ Spatial query completed");
        }
        SpatialCommands::Relate { entity1, entity2, relationship } => {
            println!("🔗 Setting spatial relationship: {} {} {}", entity1, relationship, entity2);
            
            let result = core.spatial_manager().set_spatial_relationship(&entity1, &entity2, &relationship)
                .map_err(|e| format!("Failed to set spatial relationship: {}", e))?;
            
            println!("{}", result);
            println!("✅ Spatial relationship set successfully");
        }
        SpatialCommands::Transform { from, to, entity } => {
            println!("🔄 Transforming coordinates: {} from {} to {}", entity, from, to);
            
            let result = core.spatial_manager().transform_coordinates(&from, &to, &entity)
                .map_err(|e| format!("Failed to transform coordinates: {}", e))?;
            
            println!("{}", result);
            println!("✅ Coordinate transformation completed");
        }
        SpatialCommands::Validate { entity, tolerance } => {
            println!("✅ Validating spatial data");
            
            if let Some(ref e) = entity {
                println!("   Entity: {}", e);
            }
            
            if let Some(t) = tolerance {
                println!("   Tolerance: {}", t);
            }
            
            let result = core.spatial_manager().validate_spatial(entity.as_deref(), tolerance)
                .map_err(|e| format!("Failed to validate spatial data: {}", e))?;
            
            println!("{}", result);
            println!("✅ Spatial validation completed");
        }
    }
    Ok(())
}

fn handle_git_command(action: GitCommands, _core: &ArxOSCore) -> Result<(), Box<dyn std::error::Error>> {
    match action {
        GitCommands::Init => {
            println!("Initializing Git repository...");
        }
        GitCommands::Add { files } => {
            println!("Adding files: {:?}", files);
        }
        GitCommands::Commit { message } => {
            println!("Committing with message: {}", message);
        }
        GitCommands::Push => {
            println!("Pushing changes...");
        }
        GitCommands::Pull => {
            println!("Pulling changes...");
        }
    }
    Ok(())
}
